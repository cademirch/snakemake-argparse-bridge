"""
Tests for snakemake-argparse-bridge decorator functionality
"""

import sys
import json
import subprocess
from pathlib import Path

# Add src to path
test_dir = Path(__file__).parent
src_dir = test_dir.parent / "src"
sys.path.insert(0, str(src_dir))

from snakemake_argparse_bridge import snakemake_compatible

try:
    import pytest
except ImportError:
    pytest = None


class TestCLIMode:
    """Test that decorated scripts work in normal CLI mode"""

    def test_process_sample_cli(self, tmp_path):
        """Test process_sample.py script in CLI mode"""
        # Create test input file
        input_file = tmp_path / "input.txt"
        input_file.write_text("test_data_content")

        output_file = tmp_path / "output.txt"
        log_file = tmp_path / "test.log"

        # Run the script in CLI mode
        script_path = test_dir / "scripts" / "process_sample.py"
        cmd = [
            sys.executable,
            str(script_path),
            "--input-file",
            str(input_file),
            "--output-file",
            str(output_file),
            "--sample",
            "test_sample",
            "--method",
            "advanced",
            "--threshold",
            "0.8",
            "--extra-param",
            "test_extra",
            "--log-file",
            str(log_file),
            "--threads",
            "2",
            "--memory",
            "1024",
            "--runtime",
            "30",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert (
            "Successfully processed test_sample with advanced method" in result.stdout
        )

        # Check output file was created and has expected content
        assert output_file.exists()
        content = output_file.read_text()
        assert "Sample: test_sample" in content
        assert "Method: advanced" in content
        assert "Threshold: 0.8" in content
        assert "Threads: 2" in content
        assert "Memory: 1024MB" in content
        assert (
            "ADVANCED_PROCESSED(test_data_content)_threshold_0.8_extra_test_extra"
            in content
        )

        # Check log file
        assert log_file.exists()
        log_data = json.loads(log_file.read_text())
        assert log_data["sample"] == "test_sample"
        assert log_data["method"] == "advanced"
        assert log_data["threshold"] == 0.8

    def test_summarize_results_cli(self, tmp_path):
        """Test summarize_results.py script in CLI mode"""
        # Create test input file (processed data format)
        input_file = tmp_path / "processed.txt"
        input_file.write_text("""Sample: test_sample
Method: advanced
Threshold: 0.8
Threads: 2
Memory: 1024MB
Runtime: 30min
Processed Data: ADVANCED_PROCESSED(test_data)_threshold_0.8_extra_test
""")

        output_file = tmp_path / "summary.json"
        log_file = tmp_path / "summary.log"

        # Run the script in CLI mode
        script_path = test_dir / "scripts" / "summarize_results.py"
        cmd = [
            sys.executable,
            str(script_path),
            "--input-file",
            str(input_file),
            "--output-file",
            str(output_file),
            "--sample",
            "test_sample",
            "--format",
            "json",
            "--include-stats",
            "--log-file",
            str(log_file),
            "--threads",
            "1",
            "--memory",
            "512",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        assert result.returncode == 0, f"Script failed: {result.stderr}"
        assert "Successfully summarized test_sample in json format" in result.stdout

        # Check output file
        assert output_file.exists()
        summary = json.loads(output_file.read_text())
        assert summary["sample"] == "test_sample"
        assert summary["format"] == "json"
        assert summary["threads_used"] == 1
        assert summary["memory_allocated"] == 512
        assert "stats" in summary
        assert summary["stats"]["line_count"] == 7
        assert summary["stats"]["processed_method"] == "advanced"

        # Check log file
        assert log_file.exists()
        assert "Summarized test_sample in json format" in log_file.read_text()


class TestDecoratorFunctionality:
    """Test the decorator itself with mock Snakemake context"""

    def test_decorator_without_snakemake(self):
        """Test that decorator falls back to normal argparse when no Snakemake context"""

        @snakemake_compatible(mapping={"sample": "wildcards.sample"})
        def test_function():
            import argparse

            parser = argparse.ArgumentParser()
            parser.add_argument("--sample", required=True)
            parser.add_argument("--value", type=int, default=42)

            # This should work with normal argparse since no Snakemake context
            return parser.parse_args(["--sample", "test_sample", "--value", "100"])

        args = test_function()
        assert args.sample == "test_sample"
        assert args.value == 100

    def test_decorator_preserves_function_signature(self):
        """Test that decorator preserves the original function's behavior"""

        @snakemake_compatible()
        def test_function_with_args(x, y, z=None):
            return f"x={x}, y={y}, z={z}"

        result = test_function_with_args("a", "b", z="c")
        assert result == "x=a, y=b, z=c"

    def test_decorator_restores_parse_args(self):
        """Test that decorator properly restores original parse_args method"""
        import argparse

        original_parse_args = argparse.ArgumentParser.parse_args

        @snakemake_compatible()
        def test_function():
            parser = argparse.ArgumentParser()
            parser.add_argument("--test")
            return parser.parse_args(["--test", "value"])

        # Call the decorated function
        args = test_function()
        assert args.test == "value"

        # Verify that parse_args was restored
        assert argparse.ArgumentParser.parse_args is original_parse_args

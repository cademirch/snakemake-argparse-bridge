"""
Integration test for snakemake-argparse-bridge with actual Snakemake workflow
"""

import subprocess
import os
import json
import shutil
from pathlib import Path


test_dir = Path(__file__).parent
src_dir = test_dir.parent / "src"


class TestSnakemakeIntegration:
    """Test actual Snakemake workflow execution"""

    def test_snakemake_workflow_execution(self, tmp_path):
        """Test that the Snakemake workflow runs successfully with our decorated scripts"""

        # Copy necessary files to tmp_path
        self._setup_workflow_files(tmp_path)

        # Change to tmp directory for relative paths to work
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            # Run Snakemake workflow
            cmd = [
                "snakemake",
                "--cores",
                "4",
                "--force",  # Force re-run
                "--quiet",  # Reduce output
            ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            # If other error, show details
            if result.returncode != 0:
                print(f"Snakemake stdout: {result.stdout}")
                print(f"Snakemake stderr: {result.stderr}")

            assert result.returncode == 0, f"Snakemake workflow failed: {result.stderr}"

            # Verify outputs were created
            sample1_processed = tmp_path / "output" / "sample1_processed.txt"
            sample1_summary = tmp_path / "output" / "sample1_summary.json"
            sample2_processed = tmp_path / "output" / "sample2_processed.txt"
            sample2_summary = tmp_path / "output" / "sample2_summary.json"

            assert sample1_processed.exists(), "sample1 processed file not created"
            assert sample1_summary.exists(), "sample1 summary file not created"
            assert sample2_processed.exists(), "sample2 processed file not created"
            assert sample2_summary.exists(), "sample2 summary file not created"

            # Check content of processed files
            sample1_content = sample1_processed.read_text()
            assert "Sample: sample1" in sample1_content
            assert "Method: advanced" in sample1_content  # From config.yaml
            assert "Threshold: 0.7" in sample1_content  # From config.yaml
            assert "Threads: 2" in sample1_content  # From Snakefile
            assert "Memory: 1000MB" in sample1_content  # From Snakefile resources
            assert "Runtime: 30min" in sample1_content  # From Snakefile resources
            assert "ADVANCED_PROCESSED(raw_data_for_sample1)" in sample1_content

            # Check summary files
            sample1_summary_data = json.loads(sample1_summary.read_text())
            assert sample1_summary_data["sample"] == "sample1"
            assert sample1_summary_data["format"] == "json"
            assert sample1_summary_data["threads_used"] == 1
            assert sample1_summary_data["memory_allocated"] == 500
            assert "stats" in sample1_summary_data

            # Check logs were created
            sample1_log = tmp_path / "logs" / "sample1_process.log"
            sample1_summary_log = tmp_path / "logs" / "sample1_summary.log"

            assert sample1_log.exists(), "Processing log not created"
            assert sample1_summary_log.exists(), "Summary log not created"

            # Check log content
            log_data = json.loads(sample1_log.read_text())
            assert log_data["sample"] == "sample1"
            assert log_data["method"] == "advanced"
            assert log_data["threshold"] == 0.7
            assert log_data["extra_param"] == "custom_value"

        finally:
            os.chdir(original_cwd)

    def test_dry_run_workflow(self, tmp_path):
        """Test Snakemake dry run to validate workflow syntax"""

        # Copy necessary files to tmp_path
        self._setup_workflow_files(tmp_path)

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)

            cmd = ["snakemake", "--dry-run", "--quiet"]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                print(f"Dry run stdout: {result.stdout}")
                print(f"Dry run stderr: {result.stderr}")

            assert result.returncode == 0, f"Snakemake dry run failed: {result.stderr}"

        finally:
            os.chdir(original_cwd)

    def _setup_workflow_files(self, tmp_path):
        """Copy all necessary workflow files to tmp_path"""

        # Copy Snakefile
        snakefile_src = test_dir / "Snakefile"
        snakefile_dst = tmp_path / "Snakefile"
        shutil.copy2(snakefile_src, snakefile_dst)

        # Copy config.yaml
        config_src = test_dir / "config.yaml"
        config_dst = tmp_path / "config.yaml"
        shutil.copy2(config_src, config_dst)

        # Copy scripts directory
        scripts_src = test_dir / "scripts"
        scripts_dst = tmp_path / "scripts"
        shutil.copytree(scripts_src, scripts_dst)

        # Copy data directory
        data_src = test_dir / "data"
        data_dst = tmp_path / "data"
        shutil.copytree(data_src, data_dst)

        # Create output and logs directories
        (tmp_path / "output").mkdir(exist_ok=True)
        (tmp_path / "logs").mkdir(exist_ok=True)

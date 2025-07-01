#!/usr/bin/env python3
"""
Summary script demonstrating snakemake-argparse-bridge with different directives.
"""

import argparse
import sys
import os
import json

# Add the src directory to the path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from snakemake_argparse_bridge import snakemake_compatible


@snakemake_compatible(
    mapping={
        "input_file": "input.processed",  # Named input
        "output_file": "output.summary",  # Named output
        "sample": "wildcards.sample",
        "format": "params.format",
        "include_stats": "params.include_stats",
        "log_file": "log[0]",
        "threads": "threads",
        "memory": "resources.mem_mb",
    }
)
def main():
    parser = argparse.ArgumentParser(description="Summarize processed data")
    parser.add_argument("--input-file", required=True, help="Processed data file")
    parser.add_argument("--output-file", required=True, help="Summary output file")
    parser.add_argument("--sample", required=True, help="Sample name")
    parser.add_argument(
        "--format", default="json", choices=["json", "text"], help="Output format"
    )
    parser.add_argument(
        "--include-stats", action="store_true", help="Include statistics"
    )
    parser.add_argument("--log-file", help="Log file path")
    parser.add_argument("--threads", type=int, default=1, help="Number of threads")
    parser.add_argument("--memory", type=int, help="Memory in MB")

    args = parser.parse_args()

    # Read processed data
    with open(args.input_file, "r") as f:
        lines = f.readlines()

    # Parse the processed data
    data = {}
    for line in lines:
        if ":" in line:
            key, value = line.strip().split(":", 1)
            data[key.strip()] = value.strip()

    # Create summary
    summary = {
        "sample": args.sample,
        "format": args.format,
        "threads_used": args.threads,
        "memory_allocated": args.memory,
        "original_data": data,
    }

    if args.include_stats:
        summary["stats"] = {
            "line_count": len(lines),
            "processed_method": data.get("Method", "unknown"),
            "threshold_used": data.get("Threshold", "unknown"),
        }

    # Write log if specified
    if args.log_file:
        os.makedirs(os.path.dirname(args.log_file), exist_ok=True)
        with open(args.log_file, "w") as f:
            f.write(f"Summarized {args.sample} in {args.format} format\n")

    # Create output directory if needed
    os.makedirs(os.path.dirname(args.output_file), exist_ok=True)

    # Write summary
    if args.format == "json":
        with open(args.output_file, "w") as f:
            json.dump(summary, f, indent=2)
    else:
        with open(args.output_file, "w") as f:
            f.write(f"Summary for {args.sample}\n")
            f.write("=" * 30 + "\n")
            for key, value in summary.items():
                f.write(f"{key}: {value}\n")

    print(f"Successfully summarized {args.sample} in {args.format} format")
    return 0


if __name__ == "__main__":
    sys.exit(main())

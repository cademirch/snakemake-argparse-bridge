#!/usr/bin/env python3
"""
Sample processing script demonstrating all Snakemake directives
using snakemake-argparse-bridge decorator.
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
        "input_file": "input[0]",  # First input file
        "output_file": "output[0]",  # First output file
        "sample": "wildcards.sample",
        "method": "params.method",
        "threshold": "params.threshold",
        "extra_param": "params.extra_param",
        "log_file": "log[0]",
        "threads": "threads",
        "memory": "resources.mem_mb",
        "runtime": "resources.runtime",
    }
)
def main():
    parser = argparse.ArgumentParser(description="Process sample data")
    parser.add_argument("--input-file", required=True, help="Input data file")
    parser.add_argument("--output-file", required=True, help="Output file")
    parser.add_argument("--sample", required=True, help="Sample name")
    parser.add_argument("--method", default="default", help="Processing method")
    parser.add_argument("--threshold", type=float, default=0.5, help="Threshold value")
    parser.add_argument("--extra-param", help="Extra parameter")
    parser.add_argument("--log-file", help="Log file path")
    parser.add_argument("--threads", type=int, default=1, help="Number of threads")
    parser.add_argument("--memory", type=int, help="Memory in MB")
    parser.add_argument("--runtime", type=int, help="Runtime in minutes")

    args = parser.parse_args()

    # Create log entry
    log_data = {
        "sample": args.sample,
        "method": args.method,
        "threshold": args.threshold,
        "extra_param": args.extra_param,
        "threads": args.threads,
        "memory": args.memory,
        "runtime": args.runtime,
        "input_file": args.input_file,
        "output_file": args.output_file,
    }

    # Write log if log file is specified
    if args.log_file:
        os.makedirs(os.path.dirname(args.log_file), exist_ok=True)
        with open(args.log_file, "w") as f:
            json.dump(log_data, f, indent=2)

    # Read input file
    with open(args.input_file, "r") as f:
        input_data = f.read().strip()

    # Process data based on method and threshold
    if args.method == "advanced":
        processed_data = f"ADVANCED_PROCESSED({input_data})_threshold_{args.threshold}_extra_{args.extra_param}"
    else:
        processed_data = f"PROCESSED({input_data})_threshold_{args.threshold}"

    # Create output directory if needed
    os.makedirs(os.path.dirname(args.output_file), exist_ok=True)

    # Write output
    with open(args.output_file, "w") as f:
        f.write(f"Sample: {args.sample}\n")
        f.write(f"Method: {args.method}\n")
        f.write(f"Threshold: {args.threshold}\n")
        f.write(f"Threads: {args.threads}\n")
        f.write(f"Memory: {args.memory}MB\n")
        f.write(f"Runtime: {args.runtime}min\n")
        f.write(f"Processed Data: {processed_data}\n")

    print(f"Successfully processed {args.sample} with {args.method} method")
    return 0


if __name__ == "__main__":
    sys.exit(main())

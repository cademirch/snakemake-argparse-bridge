# Snakemake Argparse Bridge

A Python package that allows existing argparse-based scripts to work seamlessly in both command-line and Snakemake environments with minimal code changes.

## Why does this exist?

You just wrote a Python script for your Snakemake rule that uses `argparse` so you can test and run it on the command line. But then when you integrate it into your workflow, you realize you need to:

1. **Rewrite the script** to work with Snakemake's `script:` directive
2. **Maintain two versions** - one for CLI testing, one for Snakemake
3. **Manually map** Snakemake variables (`wildcards`, `input`, `output`) to script arguments

This bridge eliminates that friction. Just add one decorator and your script works seamlessly in both environments.

## Installation

```bash
pip install snakemake-argparse-bridge
```

## Quick Start

### 1. Decorate your existing script

```python
# scripts/process_sample.py
import argparse
from snakemake_argparse_bridge import snakemake_compatible

@snakemake_compatible(mapping={
    'sample': 'wildcards.sample',
    'input_file': 'input[0]',
    'output_file': 'output[0]',
    'threads': 'threads'
})
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sample', required=True)
    parser.add_argument('--input-file', required=True)
    parser.add_argument('--output-file', required=True)
    parser.add_argument('--threads', type=int, default=1)
    
    # This works in both CLI and Snakemake contexts!
    args = parser.parse_args()
    
    # Your processing logic here
    print(f"Processing {args.sample} with {args.threads} threads")

if __name__ == '__main__':
    main()
```

### 2. Use in Snakemake

```python
# Snakefile
rule process_sample:
    input: "data/{sample}.txt"
    output: "results/{sample}_processed.txt"
    threads: 4
    script: "scripts/process_sample.py"
```

### 3. Still works from command line

```bash
python scripts/process_sample.py --sample test --input-file data.txt --output-file results.txt --threads 2
```

## How it works

The `@snakemake_compatible` decorator temporarily patches `argparse.ArgumentParser.parse_args()` to:

- **In Snakemake context**: Extract values from `snakemake.wildcards`, `snakemake.input`, `snakemake.params`, etc.
- **In CLI context**: Use normal argparse behavior

## Mapping Options

### Explicit Mapping

```python
@snakemake_compatible(mapping={
    'sample': 'wildcards.sample',           # Wildcard
    'input_file': 'input[0]',               # First input file
    'output_file': 'output[0]',             # First output file  
    'method': 'params.method',              # Parameter
    'threads': 'threads',                   # Thread count
    'memory': 'resources.mem_mb',           # Memory resource
    'log_file': 'log[0]',                   # Log file
})
```

## Available Snakemake Attributes

- `input`, `input[0]`, `input[1]`, etc. - Input files
- `output`, `output[0]`, `output[1]`, etc. - Output files
- `wildcards.{name}` - Wildcard values
- `params.{name}` - Rule parameters
- `log`, `log[0]`, etc. - Log files
- `threads` - Number of threads
- `resources.{name}` - Resource specifications
- `config.{name}` - Configuration values

## Testing

```bash
# Run tests
pytest tests/

# Test with actual Snakemake (requires snakemake installation)
pytest tests/test_snakemake_integration.py
```

## Requirements

- Python 3.7+
- No additional dependencies for basic usage
- Snakemake (for Snakemake integration, obviously)

## License

MIT License
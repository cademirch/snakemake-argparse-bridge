"""
A bridge package to make argparse-based scripts work seamlessly with Snakemake.
"""

import argparse
from typing import Dict, Any, Optional, Callable, Union


class SnakemakeArgparseBridge:
    """Bridge between Snakemake and argparse-based scripts."""

    def __init__(
        self,
        parser: argparse.ArgumentParser,
        mapping: Optional[Dict[str, Union[str, Callable]]] = None,
        auto_mapping: bool = True,
    ):
        """
        Initialize the bridge.

        Args:
            parser: The argparse.ArgumentParser instance
            mapping: Dict mapping argument names to snakemake attributes or callables
            auto_mapping: Whether to attempt automatic mapping based on common patterns
        """
        self.parser = parser
        self.mapping = mapping or {}
        self.auto_mapping = auto_mapping
        self._snakemake: Optional[Any] = None
        self._original_parse_args: Optional[Callable] = None

    def parse_args(self, args=None):
        """Parse arguments, using Snakemake context if available."""

        if self._detect_snakemake_context():
            return self._parse_from_snakemake()
        else:
            # Use the original parse_args to avoid recursion
            if self._original_parse_args:
                return self._original_parse_args(self.parser, args)
            else:
                return self.parser.parse_args(args)

    def _detect_snakemake_context(self) -> bool:
        """Detect if we're running within a Snakemake script context."""
        try:
            import snakemake.script

            self._snakemake = snakemake.script.snakemake
            return True
        except (ImportError, AttributeError):
            return False

    def _parse_from_snakemake(self):
        """Parse arguments from Snakemake context."""
        if self._snakemake is None:
            raise RuntimeError("Snakemake context not available")

        # create a namespace to populate
        namespace = argparse.Namespace()

        # get all actions from the parser
        for action in self.parser._actions:
            if action.dest == "help":
                continue

            arg_name = action.dest
            value = self._get_snakemake_value(arg_name)

            if value is not None:
                setattr(namespace, arg_name, value)
            elif action.default is not None:
                setattr(namespace, arg_name, action.default)
            elif action.required:
                raise ValueError(
                    f"Required argument '{arg_name}' not found in Snakemake context"
                )

        return namespace

    def _get_snakemake_value(self, arg_name: str) -> Any:
        """Get value for an argument from Snakemake context."""
        if self._snakemake is None:
            return None

        if arg_name in self.mapping:
            mapping_value = self.mapping[arg_name]
            if callable(mapping_value):
                return mapping_value(self._snakemake)
            elif isinstance(mapping_value, str):
                return self._get_nested_attr(self._snakemake, mapping_value)
            else:
                return mapping_value

        return None

    def _get_nested_attr(self, obj, attr_path: str):
        """Get nested attribute using dot notation (e.g., 'params.sample') and indexing (e.g., 'input[0]')."""
        attrs = attr_path.split(".")
        for attr in attrs:
            # handle indexing like input[0], output[1]
            if "[" in attr and attr.endswith("]"):
                attr_name, index_part = attr.split("[", 1)
                index = int(index_part.rstrip("]"))
                obj = getattr(obj, attr_name)[index]
            else:
                obj = getattr(obj, attr)
        return obj


def create_parser_bridge(
    description: Optional[str] = None,
    mapping: Optional[Dict[str, Union[str, Callable]]] = None,
    auto_mapping: bool = True,
    **parser_kwargs,
) -> SnakemakeArgparseBridge:
    """
    Create an ArgumentParser with Snakemake bridge support.

    Args:
        description: Parser description
        mapping: Argument to Snakemake attribute mapping
        auto_mapping: Enable automatic mapping
        **parser_kwargs: Additional arguments for ArgumentParser

    Returns:
        SnakemakeArgparseBridge instance
    """
    parser = argparse.ArgumentParser(description=description, **parser_kwargs)
    return SnakemakeArgparseBridge(parser, mapping, auto_mapping)


def snakemake_compatible(
    mapping: Optional[Dict[str, Union[str, Callable]]] = None, auto_mapping: bool = True
):
    """
    Decorator to make a function's argparse parsing Snakemake-compatible.

    Usage:
        @snakemake_compatible(mapping={'sample': 'wildcards.sample'})
        def main():
            parser = argparse.ArgumentParser()
            parser.add_argument('--sample', required=True)
            parser.add_argument('--input', required=True)
            parser.add_argument('--output', required=True)

            # This will work both in CLI and Snakemake contexts
            args = parser.parse_args()
            # ... rest of your code
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Intercept argparse usage in the function
            original_parse_args = argparse.ArgumentParser.parse_args

            def patched_parse_args(self, args=None, namespace=None):
                bridge = SnakemakeArgparseBridge(self, mapping, auto_mapping)
                # Store the original method on the bridge to avoid recursion
                bridge._original_parse_args = original_parse_args
                return bridge.parse_args(args)

            # Temporarily patch parse_args
            argparse.ArgumentParser.parse_args = patched_parse_args
            try:
                return func(*args, **kwargs)
            finally:
                # Restore original method
                argparse.ArgumentParser.parse_args = original_parse_args

        return wrapper

    return decorator

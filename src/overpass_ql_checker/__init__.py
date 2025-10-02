"""
Overpass QL Syntax Checker

A comprehensive Python syntax checker for the Overpass Query Language (OverpassQL).
Based on the official Overpass API documentation and language specification.

This package provides tools to validate, parse, and analyze Overpass QL queries
used to query OpenStreetMap data through the Overpass API.
"""

__version__ = "1.0.0"
__author__ = "Mark McLaren"
__email__ = "mark@example.com"  # Replace with your actual email
__license__ = "MIT"

from .checker import OverpassQLSyntaxChecker, Token, TokenType, ValidationResult
from .checker import SyntaxError as OverpassSyntaxError

__all__ = [
    "OverpassQLSyntaxChecker",
    "TokenType",
    "Token",
    "OverpassSyntaxError",
    "ValidationResult",
]

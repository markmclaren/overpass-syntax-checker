"""
Overpass QL Syntax Checker

A comprehensive Python syntax checker for the Overpass Query Language (OverpassQL).
Based on the official Overpass API documentation and language specification.

This module provides the core functionality for validating, parsing, and analyzing
Overpass QL queries used to query OpenStreetMap data through the Overpass API.
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union


class TokenType(Enum):
    """Token types for Overpass QL lexer."""

    # Literals
    STRING = "STRING"
    NUMBER = "NUMBER"
    IDENTIFIER = "IDENTIFIER"

    # Keywords
    NODE = "NODE"
    WAY = "WAY"
    REL = "REL"
    RELATION = "RELATION"
    NWR = "NWR"
    NW = "NW"
    NR = "NR"
    WR = "WR"
    AREA = "AREA"
    OUT = "OUT"
    IS_IN = "IS_IN"
    TIMELINE = "TIMELINE"
    LOCAL = "LOCAL"
    CONVERT = "CONVERT"
    MAKE = "MAKE"
    DERIVED = "DERIVED"
    MAP_TO_AREA = "MAP_TO_AREA"

    # Block statement keywords
    IF = "IF"
    ELSE = "ELSE"
    FOREACH = "FOREACH"
    FOR = "FOR"
    COMPLETE = "COMPLETE"
    RETRO = "RETRO"
    COMPARE = "COMPARE"

    # Operators
    ASSIGN = "->"
    RECURSE_UP = "<"
    RECURSE_UP_REL = "<<"
    RECURSE_DOWN = ">"
    RECURSE_DOWN_REL = ">>"
    UNION_MINUS = "-"

    # Punctuation
    SEMICOLON = ";"
    COMMA = ","
    DOT = "."
    COLON = ":"

    # Brackets
    LPAREN = "("
    RPAREN = ")"
    LBRACKET = "["
    RBRACKET = "]"
    LBRACE = "{"
    RBRACE = "}"

    # Special
    EOF = "EOF"
    NEWLINE = "NEWLINE"
    COMMENT = "COMMENT"
    WHITESPACE = "WHITESPACE"
    TEMPLATE_PLACEHOLDER = "TEMPLATE_PLACEHOLDER"

    # Regex and operators in filters
    REGEX_OP = "~"
    NOT_OP = "!"
    EQUALS = "="
    NOT_EQUALS = "!="
    NOT_REGEX_OP = "!~"

    # Logical operators
    LOGICAL_AND = "&&"
    LOGICAL_OR = "||"
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    EQUAL_EQUAL = "=="

    # Arithmetic operators
    PLUS = "+"
    MINUS = "-"
    MULTIPLY = "*"
    DIVIDE = "/"
    QUESTION = "?"

    # Settings
    SETTING_TIMEOUT = "timeout"
    SETTING_MAXSIZE = "maxsize"
    SETTING_OUT = "out"
    SETTING_BBOX = "bbox"
    SETTING_DATE = "date"
    SETTING_DIFF = "diff"
    SETTING_ADIFF = "adiff"


@dataclass
class Token:
    """Represents a token in the Overpass QL source code."""

    type: TokenType
    value: str
    line: int
    column: int

    def __str__(self):
        return f"Token({self.type.value}, '{self.value}', {self.line}:{self.column})"


class SyntaxError(Exception):
    """Custom exception for syntax errors."""

    def __init__(self, message: str, line: int = 0, column: int = 0):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"Syntax Error at line {line}, column {column}: {message}")


@dataclass
class ValidationResult:
    """Result of syntax validation."""

    valid: bool
    errors: List[str]
    warnings: List[str]
    tokens: List[str]


class OverpassQLLexer:
    """Lexical analyzer for Overpass QL."""

    # Keywords mapping
    KEYWORDS = {
        "node": TokenType.NODE,
        "way": TokenType.WAY,
        "rel": TokenType.REL,
        "relation": TokenType.RELATION,
        "nwr": TokenType.NWR,
        "nw": TokenType.NW,
        "nr": TokenType.NR,
        "wr": TokenType.WR,
        "area": TokenType.AREA,
        "out": TokenType.OUT,
        "is_in": TokenType.IS_IN,
        "timeline": TokenType.TIMELINE,
        "local": TokenType.LOCAL,
        "convert": TokenType.CONVERT,
        "make": TokenType.MAKE,
        "derived": TokenType.DERIVED,
        "map_to_area": TokenType.MAP_TO_AREA,
        "if": TokenType.IF,
        "else": TokenType.ELSE,
        "foreach": TokenType.FOREACH,
        "for": TokenType.FOR,
        "complete": TokenType.COMPLETE,
        "retro": TokenType.RETRO,
        "compare": TokenType.COMPARE,
        # Settings
        "timeout": TokenType.SETTING_TIMEOUT,
        "maxsize": TokenType.SETTING_MAXSIZE,
        "bbox": TokenType.SETTING_BBOX,
        "date": TokenType.SETTING_DATE,
        "diff": TokenType.SETTING_DIFF,
        "adiff": TokenType.SETTING_ADIFF,
    }

    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens = []

    def error(self, message: str):
        """Raise a syntax error with current position."""
        raise SyntaxError(message, self.line, self.column)

    def peek(self, offset: int = 0) -> Optional[str]:
        """Peek at character at current position + offset."""
        pos = self.pos + offset
        if pos >= len(self.text):
            return None
        return self.text[pos]

    def advance(self) -> Optional[str]:
        """Move to next character and return current."""
        if self.pos >= len(self.text):
            return None

        char = self.text[self.pos]
        self.pos += 1

        if char == "\n":
            self.line += 1
            self.column = 1
        else:
            self.column += 1

        return char

    def skip_whitespace(self):
        """Skip whitespace characters except newlines."""
        while self.peek() and self.peek() in " \t\r":
            self.advance()

    def _handle_escape_sequence(self, quote_char: str) -> str:
        """Handle escape sequences in string literals."""
        next_char = self.advance()
        if next_char == "n":
            return "\n"
        elif next_char == "t":
            return "\t"
        elif next_char == "r":
            return "\r"
        elif next_char == "\\":
            return "\\"
        elif next_char == quote_char:
            return quote_char
        elif next_char == "1":  # Handle \1 in make statements
            return "\\1"
        elif next_char and next_char.startswith("u"):
            # Unicode escape sequence \uXXXX
            return self._handle_unicode_escape()
        else:
            return next_char

    def _handle_unicode_escape(self) -> str:
        """Handle unicode escape sequence \\uXXXX."""
        unicode_digits = ""
        for _ in range(4):
            digit = self.advance()
            if digit and digit in "0123456789abcdefABCDEF":
                unicode_digits += digit
            else:
                self.error("Invalid unicode escape sequence")
        return chr(int(unicode_digits, 16))

    def read_string(self, quote_char: str) -> str:
        """Read a string literal."""
        value = ""
        self.advance()  # Skip opening quote

        while self.peek() and self.peek() != quote_char:
            char = self.advance()
            if char == "\\":
                value += self._handle_escape_sequence(quote_char)
            else:
                value += char

        if not self.peek() or self.peek() != quote_char:
            self.error("Unterminated string literal")

        self.advance()  # Skip closing quote
        return value

    def read_number(self) -> str:
        """Read a number literal."""
        value = ""

        # Handle negative numbers
        if self.peek() == "-":
            value += self.advance()

        # Read integer part
        while self.peek() and self.peek().isdigit():
            value += self.advance()

        # Read decimal part
        if self.peek() == ".":
            value += self.advance()
            while self.peek() and self.peek().isdigit():
                value += self.advance()

        # Read scientific notation
        if self.peek() and self.peek().lower() == "e":
            value += self.advance()
            if self.peek() and self.peek() in "+-":
                value += self.advance()
            while self.peek() and self.peek().isdigit():
                value += self.advance()

        return value

    def read_identifier(self) -> str:
        """Read an identifier or keyword."""
        value = ""

        # First character must be letter or underscore
        if self.peek() and (self.peek().isalpha() or self.peek() == "_"):
            value += self.advance()

        # Subsequent characters can be letters, digits, underscores, or backslashes
        while self.peek() and (self.peek().isalnum() or self.peek() in "_\\"):
            char = self.peek()
            if char == "\\":
                # Handle backslash followed by digit (like \1)
                next_char = self.peek(1)
                if next_char and next_char.isdigit():
                    value += self.advance()  # Add backslash
                    value += self.advance()  # Add digit
                else:
                    break  # Not a backslash identifier, stop
            else:
                value += self.advance()

        return value

    def read_comment(self) -> str:
        """Read a comment."""
        value = ""

        if self.peek() == "/" and self.peek(1) == "/":
            # Single-line comment
            self.advance()  # Skip first /
            self.advance()  # Skip second /

            while self.peek() and self.peek() != "\n":
                value += self.advance()

        elif self.peek() == "/" and self.peek(1) == "*":
            # Multi-line comment
            self.advance()  # Skip /
            self.advance()  # Skip *

            while self.peek():
                if self.peek() == "*" and self.peek(1) == "/":
                    self.advance()  # Skip *
                    self.advance()  # Skip /
                    break
                value += self.advance()
            else:
                self.error("Unterminated multi-line comment")

        return value

    def read_template_placeholder(self) -> str:
        """Read a template placeholder like {{bbox}}, {{geocodeArea:"name"}},
        {{date:7 days}}."""
        value = ""

        # Skip first {{
        self.advance()  # Skip first {
        self.advance()  # Skip second {
        value += "{{"

        # Read the content until we find }}
        in_string = False
        string_quote = None
        escape_next = False

        while self.peek():
            char = self.peek()

            # Handle string literals within template
            if not escape_next:
                if char in ['"', "'"]:
                    if not in_string:
                        in_string = True
                        string_quote = char
                    elif char == string_quote:
                        in_string = False
                        string_quote = None
                elif char == "\\" and in_string:
                    escape_next = True
                    value += self.advance()
                    continue
                elif char == "}" and not in_string:
                    # Check for closing }}
                    if self.peek(1) == "}":
                        self.advance()  # Skip first }
                        self.advance()  # Skip second }
                        value += "}}"
                        return value
                elif char == "\n":
                    self.error("Unterminated template placeholder, expected '}}'")
            else:
                escape_next = False

            value += self.advance()

        self.error("Unterminated template placeholder, expected '}}'")
        return value

    def _handle_two_char_operators(
        self, char: str, start_line: int, start_column: int
    ) -> bool:
        """Handle two-character operators. Returns True if handled, False otherwise."""
        # Map of (first_char, second_char) -> TokenType
        two_char_operators = {
            ("-", ">"): TokenType.ASSIGN,
            ("<", "="): TokenType.LESS_EQUAL,
            ("<", "<"): TokenType.RECURSE_UP_REL,
            (">", "="): TokenType.GREATER_EQUAL,
            (">", ">"): TokenType.RECURSE_DOWN_REL,
            ("!", "="): TokenType.NOT_EQUALS,
            ("!", "~"): TokenType.NOT_REGEX_OP,
            ("&", "&"): TokenType.LOGICAL_AND,
            ("|", "|"): TokenType.LOGICAL_OR,
            ("=", "="): TokenType.EQUAL_EQUAL,
        }

        next_char = self.peek(1)
        if next_char and (char, next_char) in two_char_operators:
            token_type = two_char_operators[(char, next_char)]
            operator = char + next_char
            self.advance()
            self.advance()
            self.tokens.append(Token(token_type, operator, start_line, start_column))
            return True

        return False

    def _handle_single_char_tokens(
        self, char: str, start_line: int, start_column: int
    ) -> bool:
        """Handle single-character tokens. Returns True if handled, False otherwise."""
        token_map = {
            ";": TokenType.SEMICOLON,
            ",": TokenType.COMMA,
            ".": TokenType.DOT,
            ":": TokenType.COLON,
            "(": TokenType.LPAREN,
            ")": TokenType.RPAREN,
            "[": TokenType.LBRACKET,
            "]": TokenType.RBRACKET,
            "}": TokenType.RBRACE,
            "<": TokenType.RECURSE_UP,
            ">": TokenType.RECURSE_DOWN,
            "-": TokenType.MINUS,  # Changed from UNION_MINUS
            "~": TokenType.REGEX_OP,
            "!": TokenType.NOT_OP,
            "=": TokenType.EQUALS,
            "+": TokenType.PLUS,
            "*": TokenType.MULTIPLY,
            "/": TokenType.DIVIDE,
            "?": TokenType.QUESTION,
        }

        if char in token_map:
            self.advance()
            self.tokens.append(Token(token_map[char], char, start_line, start_column))
            return True
        return False

    def _handle_brace_tokens(
        self, char: str, start_line: int, start_column: int
    ) -> bool:
        """Handle brace tokens including template placeholders."""
        if char == "{":
            # Check for template placeholder {{variable}}
            if self.peek(1) == "{":
                template_value = self.read_template_placeholder()
                self.tokens.append(
                    Token(
                        TokenType.TEMPLATE_PLACEHOLDER,
                        template_value,
                        start_line,
                        start_column,
                    )
                )
            else:
                self.advance()
                self.tokens.append(
                    Token(TokenType.LBRACE, "{", start_line, start_column)
                )
            return True
        return False

    def _handle_geocode_area(self) -> bool:
        """Handle geocodeArea: syntax in settings."""
        if (
            self.match(TokenType.IDENTIFIER)
            and self.current_token().value.lower() == "geocodearea"
        ):
            geocode_token = self.advance()
            if self.match(TokenType.COLON):
                self.advance()  # Skip :
                if self.match(TokenType.STRING):
                    area_name = self.advance()
                    # Create a synthetic token for geocodeArea syntax
                    geocode_value = f"{{{{geocodeArea:{area_name.value}}}}}"
                    self.tokens.append(
                        Token(
                            TokenType.TEMPLATE_PLACEHOLDER,
                            geocode_value,
                            geocode_token.line,
                            geocode_token.column,
                        )
                    )
                    return True
        return False

    def _handle_changed_filter(self) -> bool:
        """Handle changed: filter with date ranges."""
        if (
            self.match(TokenType.IDENTIFIER)
            and self.current_token().value.lower() == "changed"
        ):
            self.advance()  # Skip 'changed' token
            if self.match(TokenType.COLON):
                self.advance()  # Skip :
                if self.match(TokenType.STRING):
                    # Handle date range format: "start,end"
                    date_token = self.advance()
                    date_value = date_token.value

                    # Check if it's a date range
                    if '","' in date_value:
                        dates = date_value.split('","')
                        if len(dates) == 2:
                            # Validate both dates
                            for date in dates:
                                # Accept template placeholders like {{date:7 days}}
                                # Accept both colons and hyphens in time part (common
                                # variation)
                                iso_pattern = (
                                    r"^\d{4}-\d{2}-\d{2}T\d{2}[-:]\d{2}[-:]\d{2}Z$"
                                )
                                if not (re.match(iso_pattern, date) or "{{" in date):
                                    self.error(
                                        f"Invalid date format in changed filter: {date}"
                                    )
                            return True

                    # Single date format
                    # Accept template placeholders like {{date:7 days}}
                    # Accept both colons and hyphens in time part (common variation)
                    else:
                        iso_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}[-:]\d{2}[-:]\d{2}Z$"
                        if not (
                            re.match(iso_pattern, date_value) or "{{" in date_value
                        ):
                            self.error(
                                f"Invalid date format in changed filter: {date_value}"
                            )

                    return True
        return False

    def _handle_basic_tokens(
        self, char: str, start_line: int, start_column: int
    ) -> bool:
        """Handle basic character types. Returns True if handled."""
        # Skip whitespace
        if char in " \t\r":
            self.skip_whitespace()
            return True

        # Newlines
        elif char == "\n":
            self.advance()
            self.tokens.append(
                Token(TokenType.NEWLINE, "\\n", start_line, start_column)
            )
            return True

        # Comments
        elif char == "/" and self.peek(1) in ["/", "*"]:
            comment_text = self.read_comment()
            self.tokens.append(
                Token(TokenType.COMMENT, comment_text, start_line, start_column)
            )
            return True

        # String literals
        elif char in ['"', "'"]:
            string_value = self.read_string(char)
            self.tokens.append(
                Token(TokenType.STRING, string_value, start_line, start_column)
            )
            return True

        return False

    def _handle_numbers_and_identifiers(
        self, char: str, start_line: int, start_column: int
    ) -> bool:
        """Handle numbers and identifiers. Returns True if handled."""
        # Numbers
        if char.isdigit() or (char == "-" and self.peek(1) and self.peek(1).isdigit()):
            number_value = self.read_number()
            self.tokens.append(
                Token(TokenType.NUMBER, number_value, start_line, start_column)
            )
            return True

        # Identifiers and keywords
        elif char.isalpha() or char == "_":
            identifier = self.read_identifier()
            token_type = self.KEYWORDS.get(identifier.lower(), TokenType.IDENTIFIER)
            self.tokens.append(Token(token_type, identifier, start_line, start_column))
            return True

        return False

    def tokenize(self) -> List[Token]:
        """Tokenize the input text."""
        self.tokens = []

        while self.pos < len(self.text):
            start_line = self.line
            start_column = self.column

            char = self.peek()

            if not char:
                break

            # Handle basic token types
            if self._handle_basic_tokens(char, start_line, start_column):
                continue

            # Handle numbers and identifiers
            elif self._handle_numbers_and_identifiers(char, start_line, start_column):
                continue

            # Two-character operators
            elif self._handle_two_char_operators(char, start_line, start_column):
                continue

            # Brace tokens (including template placeholders)
            elif self._handle_brace_tokens(char, start_line, start_column):
                continue

            # Single-character tokens
            elif self._handle_single_char_tokens(char, start_line, start_column):
                continue

            else:
                self.error(f"Unexpected character: '{char}'")

        # Add EOF token
        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return self.tokens


class OverpassQLParser:
    """Parser for Overpass QL syntax checking."""

    # Valid output formats
    OUTPUT_FORMATS = {"xml", "json", "csv", "custom", "popup", "opl", "pbf"}

    # Valid out statement modes
    OUT_MODES = {"ids", "skel", "body", "tags", "meta"}

    # Valid out statement modifiers
    OUT_MODIFIERS = {"geom", "bb", "center", "asc", "qt", "noids"}

    # Valid query types
    QUERY_TYPES = {
        TokenType.NODE,
        TokenType.WAY,
        TokenType.REL,
        TokenType.RELATION,
        TokenType.NWR,
        TokenType.NW,
        TokenType.NR,
        TokenType.WR,
        TokenType.AREA,
    }

    def __init__(self, tokens: List[Token]):
        self.tokens = [
            t
            for t in tokens
            if t.type
            not in {TokenType.WHITESPACE, TokenType.COMMENT, TokenType.NEWLINE}
        ]
        self.pos = 0
        self.errors = []
        self.warnings = []

    def error(self, message: str, token: Optional[Token] = None):
        """Add an error message."""
        if token:
            error_msg = (
                f"Syntax Error at line {token.line}, column {token.column}: {message}"
            )
        else:
            current = self.current_token()
            error_msg = (
                f"Syntax Error at line {current.line}, column {current.column}: "
                f"{message}"
            )
        self.errors.append(error_msg)

    def warning(self, message: str, token: Optional[Token] = None):
        """Add a warning message."""
        if token:
            warning_msg = (
                f"Warning at line {token.line}, column {token.column}: {message}"
            )
        else:
            current = self.current_token()
            warning_msg = (
                f"Warning at line {current.line}, column {current.column}: {message}"
            )
        self.warnings.append(warning_msg)

    def current_token(self) -> Token:
        """Get current token."""
        if self.pos >= len(self.tokens):
            return self.tokens[-1]  # EOF token
        return self.tokens[self.pos]

    def peek_token(self, offset: int = 1) -> Optional[Token]:
        """Peek at token with offset."""
        pos = self.pos + offset
        if pos >= len(self.tokens):
            return None
        return self.tokens[pos]

    def match_ahead(self, *token_types: TokenType, offset: int = 1) -> bool:
        """Check if token at given offset matches any of the given types."""
        token = self.peek_token(offset)
        if token is None:
            return False
        return token.type in token_types

    def advance(self) -> Token:
        """Move to next token and return current."""
        token = self.current_token()
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return token

    def expect(self, expected_type: TokenType) -> Token:
        """Expect a specific token type."""
        token = self.current_token()
        if token.type != expected_type:
            self.error(f"Expected {expected_type.value}, got {token.type.value}")
        else:
            self.advance()
        return token

    def match(self, *token_types: TokenType) -> bool:
        """Check if current token matches any of the given types."""
        return self.current_token().type in token_types

    def _is_keyword_token(self) -> bool:
        """Check if current token is a keyword that can be used as an identifier."""
        # Keywords that can be used as set names or identifiers in certain contexts
        keyword_types = {
            TokenType.SETTING_DIFF,
            TokenType.SETTING_ADIFF,
            TokenType.SETTING_DATE,
            TokenType.NODE,
            TokenType.WAY,
            TokenType.REL,
            TokenType.RELATION,
            TokenType.AREA,
            TokenType.OUT,
            TokenType.MAKE,
            TokenType.CONVERT,
        }
        return self.current_token().type in keyword_types

    def _parse_timeout_maxsize_setting(self, setting_token: Token) -> None:
        """Parse timeout or maxsize settings."""
        self.expect(TokenType.COLON)

        if self.match(TokenType.TEMPLATE_PLACEHOLDER):
            # Allow template placeholders in settings
            self.advance()
        elif self.match(TokenType.NUMBER):
            number = self.advance()
            try:
                value = int(number.value)
                if value < 0:
                    self.error(f"{setting_token.value} must be non-negative")
            except ValueError:
                self.error(
                    f"Invalid number for {setting_token.value}: " f"{number.value}"
                )
        else:
            self.error(
                f"Expected number or template placeholder after {setting_token.value}:"
            )

    def _parse_bbox_setting(self) -> None:
        """Parse bbox setting with coordinate validation."""
        self.expect(TokenType.COLON)

        # Check if it's a template placeholder first
        if self.match(TokenType.TEMPLATE_PLACEHOLDER):
            self.advance()
            return

        # Parse bbox coordinates: south,west,north,east
        for i in range(4):
            if i > 0:
                self.expect(TokenType.COMMA)

            if not self.match(TokenType.NUMBER, TokenType.TEMPLATE_PLACEHOLDER):
                self.error(f"Expected coordinate {i + 1} in bbox")
            else:
                coord = self.advance()
                # Only validate if it's a number (skip template placeholders)
                if coord.type == TokenType.NUMBER:
                    self._validate_bbox_coordinate(coord, i)

    def _validate_bbox_coordinate(self, coord: Token, index: int) -> None:
        """Validate a single bbox coordinate."""
        try:
            coord_val = float(coord.value)
            if index in [0, 2]:  # latitude values
                if not -90 <= coord_val <= 90:
                    self.error(f"Latitude must be between -90 and 90: {coord_val}")
            else:  # longitude values
                if not -180 <= coord_val <= 180:
                    self.error(f"Longitude must be between -180 and 180: {coord_val}")
        except ValueError:
            self.error(f"Invalid coordinate: {coord.value}")

    def _parse_date_setting(self, setting_token: Token) -> None:
        """Parse date, diff, or adiff settings."""
        self.expect(TokenType.COLON)

        if not self.match(TokenType.STRING, TokenType.TEMPLATE_PLACEHOLDER):
            error_msg = (
                f"Expected date string or template placeholder after "
                f"{setting_token.value}:"
            )
            self.error(error_msg)
        else:
            date_str = self.advance()
            # Only validate if it's a string (skip template placeholders)
            if date_str.type == TokenType.STRING:
                # Basic ISO 8601 date format validation
                # Accept both colons and hyphens in time part (common variation)
                iso_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}[-:]\d{2}[-:]\d{2}Z$"
                if not (
                    re.match(iso_pattern, date_str.value) or "{{" in date_str.value
                ):
                    self.error("Invalid date format. Expected YYYY-MM-DDTHH:MM:SSZ")

    def _parse_unknown_setting(self, setting_token: Token) -> None:
        """Parse unknown settings with warning."""
        self.warning(f"Unknown setting: {setting_token.value}")

        if self.match(TokenType.COLON):
            self.advance()
            # Skip the value
            if self.match(TokenType.STRING, TokenType.NUMBER, TokenType.IDENTIFIER):
                self.advance()

    def _parse_out_setting(self) -> None:
        """Parse out setting in settings block."""
        self.advance()  # Skip 'out'
        self.expect(TokenType.COLON)

        if self.match(TokenType.IDENTIFIER):
            format_token = self.advance()
            format_name = format_token.value.lower()

            if format_name not in self.OUTPUT_FORMATS:
                self.error(f"Invalid output format: {format_token.value}")

            # Handle CSV with parameters: csv(fields; options; separator)
            if format_name == "csv" and self.match(TokenType.LPAREN):
                self._parse_csv_parameters()

        elif self.match(TokenType.STRING):
            # Could be csv with parameters
            self.advance()
        else:
            self.error("Expected output format after 'out:'")

    def _parse_csv_parameters(self) -> None:
        """Parse CSV parameters in parentheses."""
        self.advance()  # Skip (

        # Parse CSV parameters - field lists, options, separators, etc.
        # CSV format can be: csv(field1,field2,...; options; separator)
        self._parse_csv_field_list()

        # Handle optional sections separated by semicolons
        while self.match(TokenType.SEMICOLON):
            self.advance()  # Skip ;
            # Parse options or separators
            while not self.match(TokenType.SEMICOLON, TokenType.RPAREN, TokenType.EOF):
                if self.match(TokenType.STRING, TokenType.IDENTIFIER, TokenType.NUMBER):
                    self.advance()
                else:
                    break

        if self.match(TokenType.RPAREN):
            self.advance()  # Skip final )
        else:
            self.error("Expected ')' after CSV parameters")

    def _parse_csv_field_list(self) -> None:
        """Parse CSV field list (first part of CSV parameters)."""
        # Handle first field
        if self.match(TokenType.STRING, TokenType.IDENTIFIER, TokenType.COLON):
            self._parse_csv_field()

        # Handle additional fields separated by commas
        while self.match(TokenType.COMMA):
            self.advance()  # Skip comma
            if not self.match(
                TokenType.SEMICOLON, TokenType.RPAREN
            ):  # Not end of field list
                self._parse_csv_field()

    def _parse_csv_field(self) -> None:
        """Parse a single CSV field specification."""
        # Handle special field types like ::id, ::type, ::count:nodes, etc.
        if self.match(TokenType.COLON):
            self.advance()  # Skip first :
            if self.match(TokenType.COLON):
                self.advance()  # Skip second :
            # Parse field name after :: - can be identifier, string, or identifier
            # with colons
            if self.match(TokenType.STRING):
                # Handle quoted field names like ::"count:nodes"
                self.advance()
            elif self.match(TokenType.IDENTIFIER):
                self.advance()
                # Handle additional parts like :nodes, :ways, :relations after ::count
                while self.match(TokenType.COLON):
                    # Check if the next token after colon is a terminator
                    next_token = self.peek_token()
                    if next_token and next_token.type in {
                        TokenType.COMMA,
                        TokenType.SEMICOLON,
                        TokenType.RPAREN,
                    }:
                        # Don't consume the colon if it's followed by a terminator
                        break
                    self.advance()  # Skip colon
                    if self.match(TokenType.IDENTIFIER):
                        self.advance()  # Parse identifier after colon
                    else:
                        break
        # Handle quoted field names or regular identifiers
        elif self.match(TokenType.STRING, TokenType.IDENTIFIER):
            self.advance()
        else:
            # Allow any tokens in CSV field specifications for now
            # since CSV field syntax can be complex
            if not self.match(TokenType.COMMA, TokenType.SEMICOLON, TokenType.RPAREN):
                self.advance()

    def parse_settings(self) -> bool:
        """Parse settings statement."""
        if not self.match(TokenType.LBRACKET):
            return False

        # Parse all consecutive setting blocks
        while self.match(TokenType.LBRACKET):
            self.advance()  # Skip [

            # Parse individual setting within this block
            if self.match(
                TokenType.IDENTIFIER,
                TokenType.SETTING_TIMEOUT,
                TokenType.SETTING_MAXSIZE,
                TokenType.SETTING_BBOX,
                TokenType.SETTING_DATE,
                TokenType.SETTING_DIFF,
                TokenType.SETTING_ADIFF,
            ):
                setting_token = self.advance()
                setting_name = setting_token.value.lower()

                if setting_name in ["timeout", "maxsize"]:
                    self._parse_timeout_maxsize_setting(setting_token)
                elif setting_name == "bbox":
                    self._parse_bbox_setting()
                elif setting_name in ["date", "diff", "adiff"]:
                    self._parse_date_setting(setting_token)
                else:
                    self._parse_unknown_setting(setting_token)

            elif self.match(TokenType.OUT):
                self._parse_out_setting()
            else:
                self.error("Expected setting name in settings block")
                break

            self.expect(TokenType.RBRACKET)

        self._expect_optional_semicolon()
        return True

    def _parse_regex_flag(self) -> None:
        """Parse regex case insensitive flag."""
        if self.match(TokenType.COMMA):
            self.advance()
            if self.match(TokenType.IDENTIFIER):
                flag = self.advance()
                if flag.value.lower() != "i":
                    self.error(f"Invalid regex flag: {flag.value}")

    def _validate_and_parse_regex_value(
        self, op_token: Token, value_token: Token
    ) -> None:
        """Validate regex pattern and parse optional flag."""
        if op_token.type in {TokenType.REGEX_OP, TokenType.NOT_REGEX_OP}:
            # Be more permissive with regex validation since Overpass QL
            # may use different regex syntax than Python
            try:
                # Only do basic validation - check for completely malformed patterns
                pattern = value_token.value
                # Skip validation if pattern contains @ symbol (Overpass-specific
                # syntax)
                if "@" not in pattern and not pattern.strip().endswith("|"):
                    re.compile(pattern)
            except re.error as e:
                # Error on severe regex issues
                error_str = str(e)
                if any(
                    keyword in error_str
                    for keyword in [
                        "nothing to repeat",
                        "bad escape",
                        "unterminated character set",
                        "unbalanced parenthesis",
                    ]
                ):
                    self.error(f"Invalid regex pattern: {e}")
                # Warn but don't error on other regex issues
                else:
                    self.warning(f"Regex pattern may have issues: {e}")

            # Check for case insensitive flag for regex
            if op_token.type in {TokenType.REGEX_OP, TokenType.NOT_REGEX_OP}:
                self._parse_regex_flag()

    def _parse_key_value_pattern(self) -> None:
        """Parse key-value pattern like [key=value] or [key~regex]."""
        key_token = self.current_token()
        self.advance()  # Skip key

        # Special handling for temporal filters like changed:
        if key_token.value.lower() == "changed" and self.match(TokenType.COLON):
            self._parse_changed_filter()
            return

        # Check for operator
        if self.match(
            TokenType.EQUALS,
            TokenType.NOT_EQUALS,
            TokenType.REGEX_OP,
            TokenType.NOT_REGEX_OP,
        ):
            op_token = self.advance()

            # Parse value
            if self.match(TokenType.STRING, TokenType.IDENTIFIER, TokenType.NUMBER):
                value_token = self.advance()
                self._validate_and_parse_regex_value(op_token, value_token)
            else:
                self.error("Expected value after operator in tag filter")

    def _parse_changed_filter(self) -> None:
        """Parse changed filter with date range like [changed:"start","end"]."""
        self.advance()  # Skip :

        if not self.match(TokenType.STRING):
            self.error("Expected date string after 'changed:'")
            return

        first_date = self.advance()

        # Validate date format - also accept template placeholders
        # Accept both colons and hyphens in time part (common variation)
        iso_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}[-:]\d{2}[-:]\d{2}Z$"
        if not (re.match(iso_pattern, first_date.value) or "{{" in first_date.value):
            self.error(f"Invalid date format in changed filter: {first_date.value}")

        # Check for second date (range)
        if self.match(TokenType.COMMA):
            self.advance()  # Skip comma

            if not self.match(TokenType.STRING):
                self.error("Expected second date string after comma in changed filter")
                return

            second_date = self.advance()

            # Validate second date format - also accept template placeholders
            # Accept both colons and hyphens in time part (common variation)
            iso_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}[-:]\d{2}[-:]\d{2}Z$"
            if not (
                re.match(iso_pattern, second_date.value) or "{{" in second_date.value
            ):
                self.error(
                    f"Invalid date format in changed filter: {second_date.value}"
                )

    def _parse_dual_regex_pattern(self) -> None:
        """Parse dual regex pattern like [~"key-regex"~"value-regex"]."""
        self.advance()  # Skip first ~

        if not self.match(TokenType.STRING):
            self.error("Expected regex pattern after ~")
        else:
            key_regex = self.advance()
            try:
                re.compile(key_regex.value)
            except re.error as e:
                self.error(f"Invalid key regex pattern: {e}")

        if self.match(TokenType.REGEX_OP):
            self.advance()  # Skip second ~

            if not self.match(TokenType.STRING):
                self.error("Expected value regex pattern after second ~")
            else:
                value_regex = self.advance()
                try:
                    re.compile(value_regex.value)
                except re.error as e:
                    self.error(f"Invalid value regex pattern: {e}")

            # Check for case insensitive flag
            self._parse_regex_flag()

    def parse_tag_filter(self):
        """Parse tag filter [key] or [key=value] or [key~regex]."""
        self.expect(TokenType.LBRACKET)

        # Handle negation
        if self.match(TokenType.NOT_OP):
            self.advance()

        # Parse key (can be string or identifier)
        if self.match(TokenType.STRING, TokenType.IDENTIFIER):
            self._parse_key_value_pattern()
        elif self.match(TokenType.REGEX_OP):
            self._parse_dual_regex_pattern()
        else:
            self.error("Expected key name in tag filter")

        self.expect(TokenType.RBRACKET)

    def _validate_coordinate(self, coord: Token, coord_idx: int) -> None:
        """Validate a single coordinate value."""
        try:
            coord_val = float(coord.value)
            if coord_idx == 0:  # latitude
                if not -90 <= coord_val <= 90:
                    self.error(f"Latitude must be between -90 and 90: {coord_val}")
            else:  # longitude
                if not -180 <= coord_val <= 180:
                    self.error(f"Longitude must be between -180 and 180: {coord_val}")
        except ValueError:
            self.error(f"Invalid coordinate: {coord.value}")

    def _parse_around_coordinates(self) -> None:
        """Parse coordinates for around filter."""
        # Special case: {{center}} template placeholder represents a lat,lng pair
        if self.match(TokenType.TEMPLATE_PLACEHOLDER):
            placeholder = self.current_token().value
            if "center" in placeholder.lower():
                self.advance()  # Skip the {{center}} placeholder
                return

        # Parse at least one coordinate pair
        for coord_idx in range(2):  # lat, lng
            if coord_idx > 0:
                self.expect(TokenType.COMMA)

            # Accept both numbers and template placeholders like {{center}}
            if not self.match(TokenType.NUMBER, TokenType.TEMPLATE_PLACEHOLDER):
                coord_type = "latitude" if coord_idx == 0 else "longitude"
                self.error(f"Expected {coord_type}")
            else:
                coord = self.advance()
                # Only validate if it's a number (skip template placeholders)
                if coord.type == TokenType.NUMBER:
                    self._validate_coordinate(coord, coord_idx)

        # Check for additional coordinate pairs (linestring)
        while self.match(TokenType.COMMA):
            self.advance()
            if self.match(TokenType.NUMBER, TokenType.TEMPLATE_PLACEHOLDER):
                self.advance()  # Additional coordinates
            else:
                break

    def _parse_around_filter(self) -> None:
        """Parse around filter with radius and coordinates, or parameterless around."""
        if self.match(TokenType.COLON):
            self.advance()

            # Parse radius
            if not self.match(TokenType.NUMBER):
                self.error("Expected radius after 'around:'")
            else:
                radius = self.advance()
                try:
                    radius_val = float(radius.value)
                    if radius_val < 0:
                        self.error("Radius must be non-negative")
                except ValueError:
                    self.error(f"Invalid radius: {radius.value}")

            # Parse coordinates (lat,lng or multiple points) - optional for some
            # around filters
            if self.match(TokenType.COMMA):
                self.advance()
                self._parse_around_coordinates()
            # else: parameterless around filter (uses default coordinates)
        # else: around filter without explicit parameters (uses context-dependent
        # coordinates)

    def _parse_around_set_filter(self, set_name: Token) -> None:
        """Parse around filter with set reference like around.setname:distance."""
        if self.match(TokenType.COLON):
            self.advance()
            # Parse distance
            if not self.match(TokenType.NUMBER):
                self.error("Expected distance after 'around.setname:'")
            else:
                distance = self.advance()
                try:
                    distance_val = float(distance.value)
                    if distance_val < 0:
                        self.error("Distance must be non-negative")
                except ValueError:
                    self.error(f"Invalid distance: {distance.value}")

    def _parse_poly_filter(self) -> None:
        """Parse polygon filter."""
        self.expect(TokenType.COLON)
        if not self.match(TokenType.STRING):
            self.error("Expected polygon coordinate string after 'poly:'")
        else:
            poly_str = self.advance()
            # Basic validation of polygon string format
            coords = poly_str.value.split()
            if len(coords) < 6 or len(coords) % 2 != 0:
                self.error("Polygon must have at least 3 coordinate pairs")

    def _parse_area_filter(self) -> None:
        """Parse area filter."""
        # area or area.setname or area:id
        if self.match(TokenType.DOT):
            self.advance()  # Skip .
            if not self._parse_set_name():
                self.error("Expected set name after 'area.'")
        elif self.match(TokenType.COLON):
            self.advance()  # Skip :
            if not self.match(TokenType.NUMBER):
                self.error("Expected area ID after 'area:'")
            else:
                self.advance()  # Skip area ID

    def _parse_set_name(self) -> bool:
        """Parse a set name, which can be an identifier, keyword, setting name,
        or underscore."""
        # Handle special underscore case for current result set
        if self.match(TokenType.IDENTIFIER) and self.current_token().value == "_":
            self.advance()
            return True

        # Handle special keywords that can be set names
        if self.match(TokenType.IDENTIFIER) and self.current_token().value in [
            "diff",
            "result",
            "a",
            "b",
            "c",
            "area",
            "nodes",
            "ways",
            "relations",
        ]:
            self.advance()
            return True

        valid_set_name_tokens = (
            TokenType.IDENTIFIER,
            TokenType.AREA,
            TokenType.NODE,
            TokenType.WAY,
            TokenType.REL,
            TokenType.RELATION,
            TokenType.OUT,
            # Allow setting tokens to be used as set names
            TokenType.SETTING_DIFF,
            TokenType.SETTING_ADIFF,
            TokenType.SETTING_TIMEOUT,
            TokenType.SETTING_MAXSIZE,
            TokenType.SETTING_BBOX,
            TokenType.SETTING_DATE,
        )
        if self.match(*valid_set_name_tokens):
            self.advance()
            return True
        return False

    def _parse_member_filters(self, filter_name: str) -> None:
        """Parse member filters (w, r, bn, bw, br)."""
        # Handle optional .setname and :role
        if self.match(TokenType.DOT):
            self.advance()
            if self.match(TokenType.IDENTIFIER):
                self.advance()
        if self.match(TokenType.COLON):
            self.advance()
            if self.match(TokenType.STRING):
                self.advance()

    def _parse_changed_filter_spatial(self) -> None:
        """Parse changed filter with date range in spatial context."""
        self.advance()  # Skip :

        if not self.match(TokenType.STRING):
            self.error("Expected date string after 'changed:'")
            return

        first_date = self.advance()
        # Validate date format
        if not self._is_valid_date_or_template(first_date.value):
            self.error(f"Invalid date format in changed filter: {first_date.value}")

        # Check for second date (range)
        if self.match(TokenType.COMMA):
            self.advance()  # Skip comma

            if not self.match(TokenType.STRING):
                self.error("Expected second date string after comma in changed filter")
                return

            second_date = self.advance()
            # Validate second date format
            if not self._is_valid_date_or_template(second_date.value):
                self.error(
                    f"Invalid date format in changed filter: {second_date.value}"
                )

    def _parse_other_named_filters(self, filter_name: str) -> None:
        """Parse other named spatial filters."""
        # Define valid spatial filter identifiers
        valid_spatial_filters = {
            "w",
            "r",
            "bn",
            "bw",
            "br",  # member filters
            "bbox",
            "id",
            "newer",
            "user",
            "uid",
            "changed",  # other valid filters
            "nds",
            "ndr",
            "pivot",  # relation member filters
        }

        if filter_name not in valid_spatial_filters:
            self.error(f"Invalid spatial filter: '{filter_name}'")
            return

        # Handle member filters (w, r, bn, bw, br)
        if filter_name in {"w", "r", "bn", "bw", "br"}:
            self._parse_member_filters(filter_name)
        # Handle special case for changed filter with date range
        elif filter_name.lower() == "changed" and self.match(TokenType.COLON):
            self._parse_changed_filter_spatial()
        # Handle special case for id filter with comma-separated list
        elif filter_name.lower() == "id" and self.match(TokenType.COLON):
            self.advance()  # Skip ':'
            self._parse_id_list_filter()
        # Handle special case for user filter with comma-separated list
        elif filter_name.lower() == "user" and self.match(TokenType.COLON):
            self.advance()  # Skip ':'
            self._parse_user_list_filter()
        # Handle other filters with parameters
        elif self.match(TokenType.COLON):
            self.advance()
            if self.match(TokenType.STRING, TokenType.NUMBER, TokenType.IDENTIFIER):
                self.advance()

    def _validate_bbox_coordinates(self, numbers: list) -> None:
        """Validate bbox coordinates."""
        if not (-90 <= numbers[0] <= 90):  # south
            self.error(f"South latitude must be between -90 and 90: {numbers[0]}")
        if not (-180 <= numbers[1] <= 180):  # west
            self.error(f"West longitude must be between -180 and 180: {numbers[1]}")
        if not (-90 <= numbers[2] <= 90):  # north
            self.error(f"North latitude must be between -90 and 90: {numbers[2]}")
        if not (-180 <= numbers[3] <= 180):  # east
            self.error(f"East longitude must be between -180 and 180: {numbers[3]}")

    def _parse_numeric_filters(self) -> None:
        """Parse filters that start with numbers (bbox coordinates or ID list)."""
        numbers = []
        try:
            numbers.append(float(self.advance().value))  # First number

            # Count additional numbers
            while self.match(TokenType.COMMA):
                self.advance()  # Skip comma
                if self.match(TokenType.NUMBER):
                    numbers.append(float(self.advance().value))
                else:
                    break

            # Validate if it looks like a bbox (4 coordinates)
            if len(numbers) == 4:
                self._validate_bbox_coordinates(numbers)
        except ValueError as e:
            self.error(f"Invalid coordinate value: {e}")

    def _parse_id_list_filter(self) -> None:
        """Parse ID list filter."""
        if not self.match(TokenType.NUMBER):
            self.error("Expected ID after 'id:'")
        else:
            self.advance()  # First ID

            # Parse additional IDs
            while self.match(TokenType.COMMA):
                self.advance()
                if not self.match(TokenType.NUMBER):
                    self.error("Expected ID in ID list")
                else:
                    self.advance()

    def _parse_user_list_filter(self) -> None:
        """Parse user list filter."""
        if not self.match(TokenType.STRING, TokenType.TEMPLATE_PLACEHOLDER):
            self.error("Expected username string or template placeholder after 'user:'")
        else:
            self.advance()  # First username

            # Parse additional usernames
            while self.match(TokenType.COMMA):
                self.advance()
                if not self.match(TokenType.STRING, TokenType.TEMPLATE_PLACEHOLDER):
                    self.error(
                        "Expected username string or template placeholder in user list"
                    )
                else:
                    self.advance()

    def _is_valid_date_or_template(self, date_value: str) -> bool:
        """Check if a string is a valid date format or template placeholder."""
        # Check for ISO date format
        if re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", date_value):
            return True

        # Check for template placeholders like {{date:X days}} or {{date:X day}}
        if re.match(r"^\{\{date:\d+\s+(day|days)\}\}$", date_value):
            return True

        return False

    def _parse_identifier_filters(self) -> None:
        """Parse filters that start with identifiers."""
        filter_name = self.advance()

        if self.match(TokenType.COLON):
            self.advance()  # Skip :

            if filter_name.value.lower() == "id":
                self._parse_id_list_filter()
            elif filter_name.value.lower() == "changed":
                # Handle changed filter with date range: changed:"date1","date2"
                if not self.match(TokenType.STRING):
                    self.error("Expected date string after 'changed:'")
                    return

                first_date = self.advance()
                # Validate date format
                if not self._is_valid_date_or_template(first_date.value):
                    self.error(
                        f"Invalid date format in changed filter: {first_date.value}"
                    )

                # Check for second date (range)
                if self.match(TokenType.COMMA):
                    self.advance()  # Skip comma

                    if not self.match(TokenType.STRING):
                        self.error(
                            "Expected second date string after comma in changed filter"
                        )
                        return

                    second_date = self.advance()
                    # Validate second date format
                    if not self._is_valid_date_or_template(second_date.value):
                        self.error(
                            "Invalid date format in changed filter: "
                            + second_date.value
                        )
            else:
                # Other filters like newer:"date", user:"name", uid:123
                if self.match(TokenType.STRING, TokenType.NUMBER, TokenType.IDENTIFIER):
                    self.advance()

    def parse_spatial_filter(self):
        """Parse spatial filter like (bbox) or (around:radius,lat,lng)."""
        self.expect(TokenType.LPAREN)

        # Handle template placeholders like {{bbox}}
        if self.match(TokenType.TEMPLATE_PLACEHOLDER):
            self.advance()  # Skip the template placeholder token
            # Template placeholders are valid spatial filters
            self.expect(TokenType.RPAREN)
            return

        # Handle if-expressions like (if:count_by_role("outer")==1)
        if self.match(TokenType.IF):
            self._parse_if_expression()
        elif self.match(TokenType.IDENTIFIER, TokenType.AREA):
            self._parse_identifier_spatial_filter()
        # Could also be bbox coordinates or ID list
        elif self.match(TokenType.NUMBER):
            self._parse_numeric_filters()
        # Handle special filter formats like id:123,456
        elif self.match(TokenType.IDENTIFIER):
            self._parse_identifier_filters()

        self.expect(TokenType.RPAREN)

    def _parse_identifier_spatial_filter(self):
        """Parse spatial filters that start with identifiers."""
        filter_type = self.advance()
        filter_name = filter_type.value.lower()

        # Handle dotted filters like around.setname or pivot.setname
        if self.match(TokenType.DOT):
            self._parse_dotted_spatial_filter(filter_name)
        else:
            self._parse_simple_spatial_filter(filter_name)

    def _parse_dotted_spatial_filter(self, filter_name: str):
        """Parse dotted spatial filters like around.setname:distance."""
        self.advance()  # Skip .
        if not self._parse_set_name():
            self.error(f"Expected set name after '{filter_name}.'")
        else:
            # _parse_set_name() already advanced the token
            # Now handle the specific filter type with set reference
            if filter_name == "around":
                # For around.setname, we need to parse :distance
                self._parse_around_set_filter(
                    None
                )  # Pass None since we don't need the token
            elif filter_name == "pivot":
                # pivot.setname doesn't need additional parsing
                pass
            elif filter_name in {"w", "r", "bn", "bw", "br"}:
                # Member filters with set reference and optional role
                # Parse optional :role part
                if self.match(TokenType.COLON):
                    self.advance()  # Skip :
                    if self.match(TokenType.STRING):
                        self.advance()  # Skip role string
                    else:
                        self.error(
                            f"Expected role string after ':' in {filter_name} filter"
                        )
            else:
                # Other filters with set references
                pass

    def _parse_if_expression(self):
        """Parse if-expression like if:count_by_role("outer")==1."""
        self.advance()  # Skip 'if'

        # Expect colon after 'if'
        if not self.match(TokenType.COLON):
            self.error("Expected ':' after 'if'")
            return
        self.advance()  # Skip ':'

        # Parse the expression until we reach the closing parenthesis
        # For now, we'll parse it as a general expression and just skip tokens
        # A full implementation would need a proper expression parser
        paren_depth = 0
        while self.pos < len(self.tokens):
            current = self.current_token()

            if current.type == TokenType.LPAREN:
                paren_depth += 1
                self.advance()
            elif current.type == TokenType.RPAREN:
                if paren_depth == 0:
                    # This is the closing paren of the if-expression
                    break
                paren_depth -= 1
                self.advance()
            else:
                # Skip all other tokens in the expression
                self.advance()

    def _parse_simple_spatial_filter(self, filter_name: str):
        """Parse simple spatial filters without dots."""
        if filter_name == "around":
            self._parse_around_filter()
        elif filter_name == "poly":
            self._parse_poly_filter()
        elif filter_name == "area":
            self._parse_area_filter()
        else:
            self._parse_other_named_filters(filter_name)

    def parse_query_statement(self):
        """Parse query statement like node[amenity=shop](bbox)."""
        if not self.match(*self.QUERY_TYPES):
            return False

        query_type = self.current_token()
        self.advance()  # Skip query type

        # Special handling for area statements with parameter lists
        if query_type.type == TokenType.AREA and self.match(TokenType.LPAREN):
            return self._parse_area_lookup_statement()

        # Handle input set prefix (e.g., node.setname or node.set1.set2 for
        # intersection)
        while self.match(TokenType.DOT):
            self.advance()
            if not self._parse_set_name():
                self.error("Expected set name after '.'")
                break

        # Parse filters
        while self.match(TokenType.LBRACKET, TokenType.LPAREN):
            if self.match(TokenType.LBRACKET):
                self.parse_tag_filter()
            else:
                self.parse_spatial_filter()

        # Handle output assignment (->setname)
        if self.match(TokenType.ASSIGN):
            self.advance()
            if not self.match(TokenType.DOT):
                self.error("Expected '.' after '->' in assignment")
            else:
                self.advance()
                if not self._parse_set_name():
                    self.error("Expected set name after '.'")
                # No need to validate set name here, _parse_set_name handles it

        self._expect_optional_semicolon()
        return True

    def _parse_area_direct_ids(self) -> None:
        """Parse direct area IDs like area(3600062484, 123456)."""
        self.advance()  # Skip first number
        # Check for additional comma-separated IDs
        while self.match(TokenType.COMMA):
            self.advance()
            if self.match(TokenType.NUMBER):
                self.advance()
            else:
                self.error("Expected number after comma in area ID list")

    def _parse_area_named_parameter(self) -> None:
        """Parse named area parameters like area(id:123) or area(name:"value")."""
        param_name = self.advance()

        if param_name.value.lower() == "id" and self.match(TokenType.COLON):
            self.advance()  # Skip :
            self._parse_id_list_filter()
        elif self.match(TokenType.COLON):
            # Other parameter types like name:, etc.
            self.advance()  # Skip :
            if self.match(TokenType.STRING, TokenType.NUMBER, TokenType.IDENTIFIER):
                self.advance()
        else:
            self.error(f"Expected ':' after area parameter '{param_name.value}'")

    def _parse_area_lookup_statement(self) -> bool:
        """Parse area lookup statement like area(id:123,456,789) or area(123456);"""
        self.expect(TokenType.LPAREN)

        # Parse area parameters - support both direct IDs and named parameters
        if self.match(TokenType.NUMBER):
            self._parse_area_direct_ids()
        elif self.match(TokenType.IDENTIFIER):
            self._parse_area_named_parameter()
        elif self.match(TokenType.TEMPLATE_PLACEHOLDER):
            # Handle template placeholders in area lookups
            self.advance()
        else:
            self.error(
                "Expected area parameter (like 'id'), direct area ID number, "
                "or template placeholder"
            )

        self.expect(TokenType.RPAREN)

        # Handle output assignment (->setname)
        if self.match(TokenType.ASSIGN):
            self.advance()
            if not self.match(TokenType.DOT):
                self.error("Expected '.' after '->' in assignment")
            else:
                self.advance()
                if not self._parse_set_name():
                    self.error("Expected set name after '.'")

        self.expect(TokenType.SEMICOLON)
        return True

    def _handle_out_set_prefix(self, out_token: Token) -> None:
        """Handle input set prefix in out statement."""
        if self.current_token().line == out_token.line and self.match(TokenType.DOT):
            # This is actually ".setname out" format
            self.pos -= 1  # Go back

            if not self.match(TokenType.DOT):
                self.error("Expected '.' before set name")
            else:
                self.advance()
                if not self.match(TokenType.IDENTIFIER):
                    self.error("Expected set name after '.'")
                else:
                    self.advance()

            # Now expect 'out'
            self.expect(TokenType.OUT)

    def _parse_out_identifier_param(self, mode_specified: bool) -> bool:
        """Parse identifier parameters in out statement.

        Returns updated mode_specified."""
        param = self.advance()
        param_lower = param.value.lower()

        if param_lower in self.OUT_MODES:
            if mode_specified:
                self.error("Multiple output modes specified")
            return True
        elif param_lower in self.OUT_MODIFIERS:
            pass  # Valid modifier
        elif param_lower == "count":
            # Special case for 'out count'
            return mode_specified  # Don't change mode_specified, just return
        else:
            # Don't warn about unknown parameters, might be valid extensions
            pass

        return mode_specified

    def _parse_out_number_param(self) -> None:
        """Parse number parameters (limits) in out statement."""
        limit = self.advance()
        try:
            limit_val = int(limit.value)
            if limit_val < 0:
                self.error("Output limit must be non-negative")
        except ValueError:
            self.error(f"Invalid output limit: {limit.value}")

    def _parse_out_parameters(self) -> None:
        """Parse out statement parameters."""
        mode_specified = False
        while not self.match(TokenType.SEMICOLON, TokenType.EOF):
            if self.match(TokenType.IDENTIFIER):
                mode_specified = self._parse_out_identifier_param(mode_specified)
                if self.current_token().value.lower() == "count":
                    break

            elif self.match(TokenType.NUMBER):
                self._parse_out_number_param()

            elif self.match(TokenType.LPAREN):
                # Bounding box in out statement
                self.parse_spatial_filter()

            else:
                break

    def parse_out_statement(self):
        """Parse out statement."""
        if not self.match(TokenType.OUT):
            return False

        out_token = self.advance()

        # Handle input set prefix
        self._handle_out_set_prefix(out_token)

        # Parse out parameters
        self._parse_out_parameters()

        self._expect_optional_semicolon()
        return True

    def parse_union_statement(self):
        """Parse union statement (stmt1; stmt2; ...)."""
        if not self.match(TokenType.LPAREN):
            return False

        self.advance()  # Skip (

        # Parse statements inside union
        while not self.match(TokenType.RPAREN, TokenType.EOF):
            if self.match(TokenType.MINUS):
                # Difference operation (-.setname or -statement)
                self.advance()
                # Parse the statement to subtract
                if not self._parse_union_member():
                    break
                continue

            # Parse individual statement (could be a set reference, query, etc.)
            if not self._parse_union_member():
                break

        self.expect(TokenType.RPAREN)

        # Handle output assignment
        if self.match(TokenType.ASSIGN):
            self.advance()
            if not self.match(TokenType.DOT):
                self.error("Expected '.' after '->' in union assignment")
            else:
                self.advance()
                if not self._parse_set_name():
                    self.error("Expected set name after '.'")

        self._expect_optional_semicolon()
        return True

    def _parse_union_member(self) -> bool:
        """Parse a member of a union statement."""
        # Handle set references like ._ or .setname
        if self.match(TokenType.DOT):
            return self._parse_union_set_reference()
        # Handle recursion operators like >, >>, <, <<
        elif self.match(
            TokenType.RECURSE_DOWN,
            TokenType.RECURSE_DOWN_REL,
            TokenType.RECURSE_UP,
            TokenType.RECURSE_UP_REL,
        ):
            return self._parse_union_recursion_operator()
        # Handle regular statements
        else:
            return self.parse_statement()

    def _parse_union_set_reference(self) -> bool:
        """Parse a set reference in a union member (.setname with operations)."""
        self.advance()  # Skip DOT
        # Accept identifiers or keywords as set names
        if not self._parse_set_name():
            self.error("Expected set name after '.'")
            return False

        # Handle operations after set reference
        if self.match(TokenType.MAP_TO_AREA):
            self._parse_union_map_to_area_operation()
        elif self.match(
            TokenType.RECURSE_DOWN,
            TokenType.RECURSE_DOWN_REL,
            TokenType.RECURSE_UP,
            TokenType.RECURSE_UP_REL,
        ):
            self._parse_union_recursion_operation()
        elif self.match(TokenType.ASSIGN):
            if not self._parse_union_assignment():
                return False

        # Expect semicolon after set reference
        if self.match(TokenType.SEMICOLON):
            self.advance()
        return True

    def _parse_union_recursion_operator(self) -> bool:
        """Parse standalone recursion operators in union."""
        self.advance()  # Skip recursion operator
        if self.match(TokenType.SEMICOLON):
            self.advance()
        return True

    def _parse_union_map_to_area_operation(self) -> None:
        """Parse map_to_area operation after set reference."""
        self.advance()  # Skip map_to_area
        # Handle optional assignment to set
        if self.match(TokenType.ASSIGN):
            self.advance()
            if self.match(TokenType.DOT):
                self.advance()
                if not self._parse_set_name():
                    self.error("Expected set name after '->'")

    def _parse_union_recursion_operation(self) -> None:
        """Parse recursion operation after set reference."""
        self.advance()  # Skip recursion operator
        # Handle optional assignment to set
        if self.match(TokenType.ASSIGN):
            self.advance()
            if self.match(TokenType.DOT):
                self.advance()
                if not self._parse_set_name():
                    self.error("Expected set name after '->'")

    def _parse_union_assignment(self) -> bool:
        """Parse assignment after set reference (._ -> .result)."""
        self.advance()  # Skip ASSIGN
        if not self.match(TokenType.DOT):
            self.error("Expected '.' after '->' in assignment")
            return False
        self.advance()
        if not self._parse_set_name():
            self.error("Expected set name after '.'")
            return False
        return True

    def _parse_block_set_specifications(self) -> None:
        """Parse input/output set specifications for block statements."""
        # Handle input set
        if self.match(TokenType.DOT):
            self.advance()
            if not self.match(TokenType.IDENTIFIER):
                self.error("Expected set name after '.'")
            else:
                self.advance()

        # Handle output set
        if self.match(TokenType.ASSIGN):
            self.advance()
            if not self.match(TokenType.DOT):
                self.error("Expected '.' after '->'")
            else:
                self.advance()
                if not self.match(TokenType.IDENTIFIER):
                    self.error("Expected set name after '.'")
                else:
                    self.advance()

    def _parse_block_parameters(self, block_type: Token) -> None:
        """Parse parameters for specific block types."""
        if block_type.type in {
            TokenType.IF,
            TokenType.FOR,
            TokenType.RETRO,
            TokenType.COMPARE,
        }:
            if self.match(TokenType.LPAREN):
                self.advance()

                # For FOR loops, parse evaluator like t["key"]
                if block_type.type == TokenType.FOR:
                    self._parse_for_evaluator()
                else:
                    # Parse evaluator expression (simplified for other blocks)
                    while not self.match(TokenType.RPAREN, TokenType.EOF):
                        self.advance()

                self.expect(TokenType.RPAREN)

    def _parse_for_evaluator(self) -> None:
        """Parse FOR loop evaluator like t["key"], user(), keys(), etc."""
        # Handle user() pattern
        if (
            self.match(TokenType.IDENTIFIER)
            and self.current_token().value.lower() == "user"
            and self.peek_token()
            and self.peek_token().type == TokenType.LPAREN
        ):
            self.advance()  # Skip 'user'
            self.advance()  # Skip '('
            self.expect(TokenType.RPAREN)
            return

        # Handle keys() pattern
        if (
            self.match(TokenType.IDENTIFIER)
            and self.current_token().value.lower() == "keys"
            and self.peek_token()
            and self.peek_token().type == TokenType.LPAREN
        ):
            self.advance()  # Skip 'keys'
            self.advance()  # Skip '('
            self.expect(TokenType.RPAREN)
            return

        # Handle t["key"] pattern and other complex expressions
        if self.match(TokenType.IDENTIFIER):
            self.advance()

            # Parse tag filter part like ["key"] or function calls
            if self.match(TokenType.LBRACKET):
                self.advance()
                if self.match(TokenType.STRING, TokenType.IDENTIFIER):
                    self.advance()
                else:
                    self.error("Expected key name in for evaluator")
                self.expect(TokenType.RBRACKET)
            elif self.match(TokenType.LPAREN):
                # Handle function calls in for evaluator
                self.advance()  # Skip (
                # Parse function arguments
                while not self.match(TokenType.RPAREN, TokenType.EOF):
                    if self.match(
                        TokenType.STRING, TokenType.IDENTIFIER, TokenType.NUMBER
                    ):
                        self.advance()
                    elif self.match(TokenType.COMMA):
                        self.advance()
                    else:
                        break
                self.expect(TokenType.RPAREN)
        else:
            self.error("Expected evaluator identifier in for loop")

    def _parse_block_body(self) -> bool:
        """Parse block body and return whether braces were used."""
        has_braces = False

        # Handle both braces { } and parentheses ( ) for block bodies
        if self.match(TokenType.LBRACE):
            has_braces = True
            self.advance()

            while not self.match(TokenType.RBRACE, TokenType.EOF):
                if not self.parse_statement():
                    break

            self.expect(TokenType.RBRACE)
        elif self.match(TokenType.LPAREN):
            has_braces = True  # Treat parentheses like braces for semicolon handling
            self.advance()

            while not self.match(TokenType.RPAREN, TokenType.EOF):
                if not self.parse_statement():
                    break

            self.expect(TokenType.RPAREN)
        return has_braces

    def _parse_else_clause(self) -> bool:
        """Parse else clause for if statements. Returns whether braces were used."""
        has_braces = False
        if self.match(TokenType.ELSE):
            self.advance()
            if self.match(TokenType.LBRACE):
                has_braces = True
                self.advance()
                while not self.match(TokenType.RBRACE, TokenType.EOF):
                    if not self.parse_statement():
                        break
                self.expect(TokenType.RBRACE)
        return has_braces

    def parse_block_statement(self):
        """Parse block statements like if, foreach, for, etc."""
        if not self.match(
            TokenType.IF,
            TokenType.FOREACH,
            TokenType.FOR,
            TokenType.COMPLETE,
            TokenType.RETRO,
            TokenType.COMPARE,
        ):
            return False

        block_type = self.advance()

        # Handle input/output set specifications
        self._parse_block_set_specifications()

        # Parse parameters for specific block types
        self._parse_block_parameters(block_type)

        # Parse block body
        has_braces = self._parse_block_body()

        # Handle else clause for if statements
        if block_type.type == TokenType.IF:
            has_braces = self._parse_else_clause() or has_braces

        # Semicolon handling: optional for braced statements, required for non-braced
        if has_braces:
            # For braced statements, semicolon is completely optional
            if self.match(TokenType.SEMICOLON):
                self.advance()
        else:
            # For non-braced statements, semicolon is required
            self.expect(TokenType.SEMICOLON)

        return True

    def _parse_set_assignment(self) -> None:
        """Parse output set assignment (->setname)."""
        if self.match(TokenType.ASSIGN):
            self.advance()
            if not self.match(TokenType.DOT):
                self.error("Expected '.' after '->'")
            else:
                self.advance()
                if not self.match(TokenType.IDENTIFIER):
                    self.error("Expected set name after '.'")
                else:
                    self.advance()

    def _parse_input_set(self) -> None:
        """Parse input set specification (.setname)."""
        if self.match(TokenType.DOT):
            self.advance()
            if not self.match(TokenType.IDENTIFIER):
                self.error("Expected set name after '.'")
            else:
                self.advance()

    def _parse_recursion_statement(self) -> bool:
        """Parse recursion operators."""
        if self.match(
            TokenType.RECURSE_UP,
            TokenType.RECURSE_UP_REL,
            TokenType.RECURSE_DOWN,
            TokenType.RECURSE_DOWN_REL,
        ):
            self.advance()  # Skip recursion operator

            # Handle input set
            self._parse_input_set()

            # Handle output assignment
            self._parse_set_assignment()

            self.expect(TokenType.SEMICOLON)
            return True
        return False

    def _parse_is_in_coordinates(self) -> None:
        """Parse coordinates for is_in statement."""
        if self.match(TokenType.LPAREN):
            self.advance()

            # Parse lat, lng
            if not self.match(TokenType.NUMBER):
                self.error("Expected latitude in is_in statement")
            else:
                self.advance()

            self.expect(TokenType.COMMA)

            if not self.match(TokenType.NUMBER):
                self.error("Expected longitude in is_in statement")
            else:
                self.advance()

            self.expect(TokenType.RPAREN)

    def _parse_is_in_statement(self) -> bool:
        """Parse is_in statement."""
        if self.match(TokenType.IS_IN):
            self.advance()

            # Handle coordinates
            self._parse_is_in_coordinates()

            # Handle output assignment
            self._parse_set_assignment()

            self.expect(TokenType.SEMICOLON)
            return True
        return False

    def _parse_set_reference(self) -> bool:
        """Parse set reference (.setname;) with optional operations."""
        if self.match(TokenType.DOT):
            self.advance()
            if not self._parse_set_name():
                self.error("Expected set name after '.'")
                return False

            # Handle operations after set reference
            if self.match(
                TokenType.RECURSE_DOWN,
                TokenType.RECURSE_DOWN_REL,
                TokenType.RECURSE_UP,
                TokenType.RECURSE_UP_REL,
            ):
                self._parse_set_reference_recursion_operation()
            elif self.match(TokenType.MAP_TO_AREA):
                self._parse_set_reference_map_to_area_operation()
            elif self.match(TokenType.IS_IN):
                self._parse_set_reference_is_in_operation()

            self._expect_optional_semicolon()
            return True
        return False

    def _parse_set_reference_recursion_operation(self) -> None:
        """Parse recursion operation after set reference."""
        self.advance()  # Skip recursion operator
        # Handle optional assignment to set
        if self.match(TokenType.ASSIGN):
            self.advance()
            if self.match(TokenType.DOT):
                self.advance()
                if not self._parse_set_name():
                    self.error("Expected set name after '->'")

    def _parse_set_reference_map_to_area_operation(self) -> None:
        """Parse map_to_area operation after set reference."""
        self.advance()  # Skip map_to_area
        # Handle optional assignment to set
        if self.match(TokenType.ASSIGN):
            self.advance()
            if self.match(TokenType.DOT):
                self.advance()
                if not self._parse_set_name():
                    self.error("Expected set name after '->'")

    def _parse_set_reference_is_in_operation(self) -> None:
        """Parse is_in operation after set reference."""
        self.advance()  # Skip is_in
        # Handle optional assignment to set
        if self.match(TokenType.ASSIGN):
            self.advance()
            if self.match(TokenType.DOT):
                self.advance()
                if not self._parse_set_name():
                    self.error("Expected set name after '->'")
        # Handle optional coordinates (for is_in with coordinates)
        elif self.match(TokenType.LPAREN):
            self._parse_is_in_coordinates()
            # Handle optional assignment after coordinates
            if self.match(TokenType.ASSIGN):
                self.advance()
                if self.match(TokenType.DOT):
                    self.advance()
                    if not self._parse_set_name():
                        self.error("Expected set name after '->'")

    def parse_simple_statement(self):
        """Parse simple statements like recursion operators, is_in, etc."""
        # Handle template placeholders as standalone statements
        if self.match(TokenType.TEMPLATE_PLACEHOLDER):
            return self._parse_template_placeholder_statement()

        # Handle convert statements
        if self.match(TokenType.CONVERT):
            self._parse_convert_statement()
            return True

        # Handle make statements
        if self.match(TokenType.MAKE):
            self._parse_make_statement()
            return True

        # Handle map_to_area statements
        if self.match(TokenType.MAP_TO_AREA):
            self._parse_map_to_area_statement()
            return True

        # Try different statement types
        return self._try_other_simple_statements()

    def _expect_optional_semicolon(self):
        """Expect a semicolon but make it optional at end of query or before
        closing braces."""
        if self.match(TokenType.SEMICOLON):
            self.advance()
        elif not self.match(TokenType.EOF, TokenType.RBRACE, TokenType.RPAREN):
            # Only require semicolon if not at end of input or closing construct
            self.expect(TokenType.SEMICOLON)

    def _parse_template_placeholder_statement(self) -> bool:
        """Parse template placeholder statements."""
        template_token = self.advance()

        # Handle template assignments like {{bbox=area:3606195356}}
        template_value = template_token.value
        if (
            "=" in template_value
            and template_value.startswith("{{")
            and template_value.endswith("}}")
        ):
            # This is a template assignment, no semicolon required
            return True

        # Check if template placeholder is followed by tag filters (like geocodeArea)
        while self.match(TokenType.LBRACKET):
            self.parse_tag_filter()

        # Optional assignment operator
        if self.match(TokenType.ASSIGN):
            self.advance()
            if self.match(TokenType.DOT):
                self.advance()
                # Allow keywords as set names in template assignments
                if self.match(TokenType.IDENTIFIER) or self.match(
                    TokenType.AREA,
                    TokenType.NODE,
                    TokenType.WAY,
                    TokenType.REL,
                    TokenType.RELATION,
                    TokenType.OUT,
                ):
                    self.advance()
                else:
                    self.error("Expected set name after '.'")

        # Make semicolon optional for template statements
        self._expect_optional_semicolon()
        return True

    def _try_other_simple_statements(self) -> bool:
        """Try parsing other types of simple statements."""
        if self._parse_recursion_statement():
            return True
        elif self._parse_is_in_statement():
            return True
        elif self._parse_set_reference():
            return True
        return False

    def _parse_make_statement(self) -> None:
        """Parse make statement: make identifier [,]key=value,...;"""
        self.advance()  # Skip 'make'

        # Parse identifier (can contain backslashes like stat_highway_\1)
        if not self.match(TokenType.IDENTIFIER):
            self.error("Expected identifier after 'make'")
            return
        self.advance()

        # Parse optional comma after identifier
        if self.match(TokenType.COMMA):
            self.advance()

        # Parse key=value pairs
        first_pair = True
        while (
            first_pair
            and (self.match(TokenType.IDENTIFIER) or self.match(TokenType.STRING))
        ) or (not first_pair and self.match(TokenType.COMMA)):
            if not first_pair:
                self.advance()  # Skip comma
            first_pair = False

            # Parse key (can be string or identifier)
            if not (self.match(TokenType.IDENTIFIER) or self.match(TokenType.STRING)):
                self.error("Expected key in make statement")
                return
            self.advance()

            # Parse equals
            if not self.match(TokenType.EQUALS):
                self.error("Expected '=' in make statement")
                return
            self.advance()

            # Parse value expression (can be function calls, etc.)
            self._parse_make_value_expression()

        self._expect_optional_semicolon()

    def _parse_make_value_expression(self) -> None:
        """Parse value expression in make statement."""
        self._parse_make_ternary_expression()

    def _parse_make_ternary_expression(self) -> None:
        """Parse ternary expressions (condition ? true_value : false_value)."""
        self._parse_make_comparison_expression()

        # Handle ternary operator
        if self.match(TokenType.QUESTION):
            self.advance()  # Skip ?
            self._parse_make_comparison_expression()  # true value
            if self.match(TokenType.COLON):
                self.advance()  # Skip :
                self._parse_make_comparison_expression()  # false value
            else:
                self.error("Expected ':' in ternary expression")

    def _parse_make_comparison_expression(self) -> None:
        """Parse comparison expressions (==, !=, <, >, <=, >=)."""
        self._parse_make_additive_expression()

        while self.match(
            TokenType.EQUAL_EQUAL,
            TokenType.NOT_EQUALS,
            TokenType.LESS_THAN,
            TokenType.GREATER_THAN,
            TokenType.LESS_EQUAL,
            TokenType.GREATER_EQUAL,
        ):
            self.advance()  # Skip operator
            self._parse_make_additive_expression()

    def _parse_make_additive_expression(self) -> None:
        """Parse additive expressions (+ and -)."""
        self._parse_make_multiplicative_expression()

        while self.match(TokenType.PLUS, TokenType.MINUS):
            self.advance()  # Skip operator
            self._parse_make_multiplicative_expression()

    def _parse_make_multiplicative_expression(self) -> None:
        """Parse multiplicative expressions (* and /)."""
        self._parse_make_primary_expression()

        while self.match(TokenType.MULTIPLY, TokenType.DIVIDE):
            self.advance()  # Skip operator
            self._parse_make_primary_expression()

    def _parse_make_primary_expression(self) -> None:
        """Parse primary expressions (function calls, identifiers, numbers, strings)."""
        # Handle function calls like count(ways), length(sum(length()))
        if (
            self.match(TokenType.IDENTIFIER)
            and self.peek_ahead(1)
            and self.peek_ahead(1).type == TokenType.LPAREN
        ):
            self.advance()  # Function name
            self.expect(TokenType.LPAREN)

            # Parse function arguments (can be nested)
            if not self.match(TokenType.RPAREN):
                self._parse_make_function_args()

            self.expect(TokenType.RPAREN)
        # Handle complex expressions like _.val
        elif self.match(TokenType.IDENTIFIER):
            self.advance()
            # Handle tag access like t["key"]
            if self.match(TokenType.LBRACKET):
                self.advance()  # Skip [
                if self.match(TokenType.STRING):
                    self.advance()  # Skip string key
                else:
                    self.error("Expected string key in tag access")
                self.expect(TokenType.RBRACKET)
            # Handle dotted access like _.val
            elif self.match(TokenType.DOT):
                self.advance()
                if self.match(TokenType.IDENTIFIER):
                    self.advance()
                else:
                    self.error("Expected identifier after '.' in expression")
        # Handle simple values
        elif self.match(TokenType.NUMBER, TokenType.STRING):
            self.advance()
        # Handle parenthesized expressions
        elif self.match(TokenType.LPAREN):
            self.advance()  # Skip (
            self._parse_make_value_expression()
            self.expect(TokenType.RPAREN)
        else:
            self.error("Expected value expression in make statement")

    def _parse_make_function_args(self) -> None:
        """Parse function arguments in make statement."""
        while True:
            # Parse argument (can be function call, expression, or simple value)
            self._parse_make_value_expression()

            if self.match(TokenType.COMMA):
                self.advance()
            else:
                break

    def peek_ahead(self, offset: int) -> Optional[Token]:
        """Peek ahead at token with offset."""
        pos = self.pos + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return None

    def _parse_convert_statement(self) -> None:
        """Parse convert statement."""
        self.advance()  # Skip 'convert' token

        # Convert statements can have various formats:
        # convert geometry ::id=id()
        # convert row ::id=id(),...
        # convert item

        # First part can be 'geometry', 'row', 'item', or other identifiers
        if self.match(TokenType.IDENTIFIER):
            self.advance()  # Skip the convert type

        # Parse assignment patterns
        self._parse_convert_assignments()
        self.expect(TokenType.SEMICOLON)

    def _parse_convert_assignments(self) -> None:
        """Parse assignment patterns in convert statements."""
        # Handle first assignment (may not have comma before it)
        if self.match(TokenType.IDENTIFIER) or self.match(TokenType.COLON):
            self._parse_convert_single_assignment()

        # Handle additional assignments separated by commas
        while self.match(TokenType.COMMA):
            self.advance()  # Skip comma
            if self.match(TokenType.IDENTIFIER) or self.match(TokenType.COLON):
                self._parse_convert_single_assignment()
            else:
                break

    def _parse_convert_single_assignment(self) -> None:
        """Parse a single assignment in a convert statement."""
        # Handle ::id syntax or ::=id() syntax
        if self.match(TokenType.COLON):
            self.advance()  # Skip first :
            if self.match(TokenType.COLON):
                self.advance()  # Skip second :
                # Handle ::= syntax (double colon equals)
                if self.match(TokenType.EQUALS):
                    self.advance()  # Skip =
                    # Parse value expression after ::=
                    self._parse_convert_assignment_value()
                    return
            else:
                # Single colon, rewind
                self.pos -= 1

        # Parse the identifier
        if not self.match(TokenType.IDENTIFIER):
            self.error("Expected identifier in convert assignment")
            return
        self.advance()  # Skip identifier

        # Expect equals sign
        if not self.match(TokenType.EQUALS):
            self.error("Expected '=' in convert assignment")
            return
        self.advance()  # Skip =

        # Parse the value expression (can be function calls, etc.)
        self._parse_convert_assignment_value()

    def _parse_convert_assignment_value(self) -> None:
        """Parse the value part of a convert assignment."""
        # Reuse the sophisticated expression parsing from make statements
        self._parse_make_value_expression()

    def _parse_parentheses_content(self) -> None:
        """Parse content inside parentheses, handling nested parentheses."""
        self.advance()  # Skip opening (
        paren_count = 1
        while paren_count > 0 and not self.match(TokenType.EOF):
            if self.match(TokenType.LPAREN):
                paren_count += 1
            elif self.match(TokenType.RPAREN):
                paren_count -= 1
            self.advance()

    def _parse_map_to_area_statement(self) -> None:
        """Parse map_to_area statement."""
        self.advance()  # Skip 'map_to_area' token

        # Optional assignment to set
        if self.match(TokenType.ASSIGN):
            self.advance()
            if self.match(TokenType.DOT):
                self.advance()
                if not self._parse_set_name():
                    self.error("Expected set name after '->'")
            else:
                self.error("Expected '.' after '->' in map_to_area statement")

        self.expect(TokenType.SEMICOLON)

    def _is_set_reference_out_statement(self) -> bool:
        """Check if current position is a set reference followed by out."""
        peek1 = self.peek_token(1)
        peek2 = self.peek_token(2)
        return (
            self.match(TokenType.DOT)
            and peek1
            and (peek1.type == TokenType.IDENTIFIER or self._is_keyword_token_at(1))
            and peek2
            and peek2.type == TokenType.OUT
        )

    def _is_keyword_token_at(self, offset: int) -> bool:
        """Check if token at offset is a keyword that can be used as identifier."""
        token = self.peek_token(offset)
        if not token:
            return False
        keyword_types = {
            TokenType.SETTING_DIFF,
            TokenType.SETTING_ADIFF,
            TokenType.SETTING_DATE,
            TokenType.NODE,
            TokenType.WAY,
            TokenType.REL,
            TokenType.RELATION,
            TokenType.AREA,
            TokenType.OUT,
            TokenType.MAKE,
            TokenType.CONVERT,
        }
        return token.type in keyword_types

    def _parse_set_reference_out(self) -> bool:
        """Parse set reference followed by out statement."""
        self.advance()  # Skip .
        if not self._parse_set_name():
            self.error("Expected set name after '.'")
            return False
        # Now parse the out statement
        return self.parse_out_statement()

    def _parse_standalone_recursion(self) -> bool:
        """Parse standalone recursion operators."""
        if self.match(
            TokenType.RECURSE_DOWN,
            TokenType.RECURSE_DOWN_REL,
            TokenType.RECURSE_UP,
            TokenType.RECURSE_UP_REL,
        ):
            self.advance()
            self._expect_optional_semicolon()
            return True
        return False

    def parse_statement(self) -> bool:
        """Parse any statement."""
        # Skip any leading comments or newlines
        while self.match(TokenType.COMMENT, TokenType.NEWLINE):
            self.advance()

        if self.match(TokenType.EOF):
            return False

        # Try different statement types
        if self._is_set_reference_out_statement():
            return self._parse_set_reference_out()
        elif self.parse_query_statement():
            return True
        elif self.parse_out_statement():
            return True
        elif self.parse_union_statement():
            return True
        elif self.parse_block_statement():
            return True
        elif self.parse_simple_statement():
            return True
        elif self._parse_standalone_recursion():
            return True
        else:
            self.error(f"Unexpected token: {self.current_token().value}")
            self.advance()  # Skip the unexpected token
            return False

    def parse(self) -> Tuple[List[str], List[str]]:
        """Parse the entire query and return errors and warnings."""
        self.errors = []
        self.warnings = []

        # Check for settings at the beginning
        first_non_comment = 0

        # Skip initial comments and newlines
        while first_non_comment < len(self.tokens) and self.tokens[
            first_non_comment
        ].type in {TokenType.COMMENT, TokenType.NEWLINE}:
            first_non_comment += 1

        # Check for template assignments at the very start
        if (
            first_non_comment < len(self.tokens)
            and self.tokens[first_non_comment].type == TokenType.TEMPLATE_PLACEHOLDER
        ):
            self.pos = first_non_comment
            template_token = self.tokens[self.pos]
            if "=" in template_token.value:
                # Parse template assignment
                self.advance()
                # Continue to parse settings/statements after template assignment

        # Check if first statement is settings
        if (
            self.pos < len(self.tokens)
            and self.tokens[self.pos].type == TokenType.LBRACKET
        ):
            self.parse_settings()

        # Parse remaining statements
        while not self.match(TokenType.EOF):
            if not self.parse_statement():
                break

        return self.errors, self.warnings


class OverpassQLSyntaxChecker:
    """Main syntax checker class for Overpass QL."""

    def __init__(self):
        self.lexer = None
        self.parser = None

    def check_syntax(self, query: str) -> Dict[str, Union[bool, List[str]]]:
        """
        Check the syntax of an Overpass QL query.

        Args:
            query: The Overpass QL query string to check

        Returns:
            Dictionary with 'valid', 'errors', 'warnings', and 'tokens' keys
        """
        result = {"valid": True, "errors": [], "warnings": [], "tokens": []}

        try:
            # Tokenize
            self.lexer = OverpassQLLexer(query)
            tokens = self.lexer.tokenize()
            result["tokens"] = [str(token) for token in tokens]

            # Parse
            self.parser = OverpassQLParser(tokens)
            errors, warnings = self.parser.parse()

            result["errors"] = errors
            result["warnings"] = warnings
            result["valid"] = len(errors) == 0

        except SyntaxError as e:
            result["valid"] = False
            result["errors"] = [str(e)]
        except Exception as e:
            result["valid"] = False
            result["errors"] = [f"Unexpected error: {str(e)}"]

        return result

    def validate_query(self, query: str, verbose: bool = False) -> bool:
        """
        Validate a query and print results.

        Args:
            query: The query to validate
            verbose: Whether to print detailed information

        Returns:
            True if query is valid, False otherwise
        """
        result = self.check_syntax(query)

        if verbose:
            print(
                f"Query validation result: "
                f"{'VALID' if result['valid'] else 'INVALID'}"
            )
            print(f"Errors: {len(result['errors'])}")
            print(f"Warnings: {len(result['warnings'])}")

            if result["errors"]:
                print("\nERRORS:")
                for error in result["errors"]:
                    print(f"  {error}")

            if result["warnings"]:
                print("\nWARNINGS:")
                for warning in result["warnings"]:
                    print(f"  {warning}")

            if verbose and result["tokens"]:
                print(f"\nTOKENS ({len(result['tokens'])}):")
                for token in result["tokens"][:20]:  # Limit output
                    print(f"  {token}")
                if len(result["tokens"]) > 20:
                    print(f"  ... and {len(result['tokens']) - 20} more tokens")

        return result["valid"]

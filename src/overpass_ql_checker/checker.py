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
        """Read a template placeholder like {{bbox}} or {{geocodeArea:"name"}}."""
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
        if char == "-" and self.peek(1) == ">":
            self.advance()
            self.advance()
            self.tokens.append(Token(TokenType.ASSIGN, "->", start_line, start_column))
            return True
        elif char == "<" and self.peek(1) == "<":
            self.advance()
            self.advance()
            self.tokens.append(
                Token(TokenType.RECURSE_UP_REL, "<<", start_line, start_column)
            )
            return True
        elif char == ">" and self.peek(1) == ">":
            self.advance()
            self.advance()
            self.tokens.append(
                Token(TokenType.RECURSE_DOWN_REL, ">>", start_line, start_column)
            )
            return True
        elif char == "!" and self.peek(1) == "=":
            self.advance()
            self.advance()
            self.tokens.append(
                Token(TokenType.NOT_EQUALS, "!=", start_line, start_column)
            )
            return True
        elif char == "!" and self.peek(1) == "~":
            self.advance()
            self.advance()
            self.tokens.append(
                Token(TokenType.NOT_REGEX_OP, "!~", start_line, start_column)
            )
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
            "-": TokenType.UNION_MINUS,
            "~": TokenType.REGEX_OP,
            "!": TokenType.NOT_OP,
            "=": TokenType.EQUALS,
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
                                if not re.match(
                                    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", date
                                ):
                                    self.error(
                                        f"Invalid date format in changed filter: {date}"
                                    )
                            return True

                    # Single date format
                    elif not re.match(
                        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", date_value
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
    OUTPUT_FORMATS = {"xml", "json", "csv", "custom", "popup"}

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

    def _parse_timeout_maxsize_setting(self, setting_token: Token) -> None:
        """Parse timeout or maxsize settings."""
        self.expect(TokenType.COLON)

        if not self.match(TokenType.NUMBER):
            self.error(f"Expected number after {setting_token.value}:")
        else:
            number = self.advance()
            try:
                value = int(number.value)
                if value < 0:
                    self.error(f"{setting_token.value} must be non-negative")
            except ValueError:
                self.error(
                    f"Invalid number for {setting_token.value}: " f"{number.value}"
                )

    def _parse_bbox_setting(self) -> None:
        """Parse bbox setting with coordinate validation."""
        self.expect(TokenType.COLON)

        # Parse bbox coordinates: south,west,north,east
        for i in range(4):
            if i > 0:
                self.expect(TokenType.COMMA)

            if not self.match(TokenType.NUMBER):
                self.error(f"Expected coordinate {i + 1} in bbox")
            else:
                coord = self.advance()
                try:
                    coord_val = float(coord.value)
                    if i in [0, 2]:  # latitude values
                        if not -90 <= coord_val <= 90:
                            self.error(
                                f"Latitude must be between -90 and 90: " f"{coord_val}"
                            )
                    else:  # longitude values
                        if not -180 <= coord_val <= 180:
                            self.error(
                                f"Longitude must be between -180 and 180: "
                                f"{coord_val}"
                            )
                except ValueError:
                    self.error(f"Invalid coordinate: {coord.value}")

    def _parse_date_setting(self, setting_token: Token) -> None:
        """Parse date, diff, or adiff settings."""
        self.expect(TokenType.COLON)

        if not self.match(TokenType.STRING):
            self.error(f"Expected date string after {setting_token.value}:")
        else:
            date_str = self.advance()
            # Basic ISO 8601 date format validation
            if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", date_str.value):
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

        # Parse CSV parameters - this is simplified parsing
        # In real Overpass QL, this has complex field specifications
        while not self.match(TokenType.RPAREN, TokenType.EOF):
            # Skip any tokens until we find the closing paren
            # This handles field lists, options, separators, etc.
            self.advance()

        if self.match(TokenType.RPAREN):
            self.advance()  # Skip )
        else:
            self.error("Expected ')' after CSV parameters")

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

        self.expect(TokenType.SEMICOLON)
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
            try:
                re.compile(value_token.value)
            except re.error as e:
                self.error(f"Invalid regex pattern: {e}")

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

        # Validate date format
        if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", first_date.value):
            self.error(f"Invalid date format in changed filter: {first_date.value}")

        # Check for second date (range)
        if self.match(TokenType.COMMA):
            self.advance()  # Skip comma

            if not self.match(TokenType.STRING):
                self.error("Expected second date string after comma in changed filter")
                return

            second_date = self.advance()

            # Validate second date format
            if not re.match(
                r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", second_date.value
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
        # Parse at least one coordinate pair
        for coord_idx in range(2):  # lat, lng
            if coord_idx > 0:
                self.expect(TokenType.COMMA)

            if not self.match(TokenType.NUMBER):
                coord_type = "latitude" if coord_idx == 0 else "longitude"
                self.error(f"Expected {coord_type}")
            else:
                coord = self.advance()
                self._validate_coordinate(coord, coord_idx)

        # Check for additional coordinate pairs (linestring)
        while self.match(TokenType.COMMA):
            self.advance()
            if self.match(TokenType.NUMBER):
                self.advance()  # Additional coordinates
            else:
                break

    def _parse_around_filter(self) -> None:
        """Parse around filter with radius and coordinates."""
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

            # Parse coordinates (lat,lng or multiple points)
            self.expect(TokenType.COMMA)
            self._parse_around_coordinates()

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
            if not self.match(TokenType.IDENTIFIER):
                self.error("Expected set name after 'area.'")
            else:
                self.advance()  # Skip set name
        elif self.match(TokenType.COLON):
            self.advance()  # Skip :
            if not self.match(TokenType.NUMBER):
                self.error("Expected area ID after 'area:'")
            else:
                self.advance()  # Skip area ID

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
        if not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", first_date.value):
            self.error(f"Invalid date format in changed filter: {first_date.value}")

        # Check for second date (range)
        if self.match(TokenType.COMMA):
            self.advance()  # Skip comma

            if not self.match(TokenType.STRING):
                self.error("Expected second date string after comma in changed filter")
                return

            second_date = self.advance()
            # Validate second date format
            if not re.match(
                r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", second_date.value
            ):
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
                if not re.match(
                    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", first_date.value
                ):
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
                    if not re.match(
                        r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", second_date.value
                    ):
                        self.error(
                            f"Invalid date format in changed filter: {
                                second_date.value}"
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

        if self.match(TokenType.IDENTIFIER, TokenType.AREA):
            filter_type = self.advance()
            filter_name = filter_type.value.lower()

            if filter_name == "around":
                self._parse_around_filter()
            elif filter_name == "poly":
                self._parse_poly_filter()
            elif filter_name == "area":
                self._parse_area_filter()
            else:
                self._parse_other_named_filters(filter_name)

        # Could also be bbox coordinates or ID list
        elif self.match(TokenType.NUMBER):
            self._parse_numeric_filters()

        # Handle special filter formats like id:123,456
        elif self.match(TokenType.IDENTIFIER):
            self._parse_identifier_filters()

        self.expect(TokenType.RPAREN)

    def parse_query_statement(self):
        """Parse query statement like node[amenity=shop](bbox)."""
        if not self.match(*self.QUERY_TYPES):
            return False

        self.advance()  # Skip query type

        # Handle input set prefix (e.g., node.setname)
        if self.match(TokenType.DOT):
            self.advance()
            if not self.match(TokenType.IDENTIFIER):
                self.error("Expected set name after '.'")
            else:
                self.advance()

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
                if not self.match(TokenType.IDENTIFIER):
                    self.error("Expected set name after '.'")
                else:
                    set_name = self.advance()
                    # Validate set name
                    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", set_name.value):
                        self.error(f"Invalid set name: {set_name.value}")

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

        self.expect(TokenType.SEMICOLON)
        return True

    def parse_union_statement(self):
        """Parse union statement (stmt1; stmt2; ...)."""
        if not self.match(TokenType.LPAREN):
            return False

        self.advance()  # Skip (

        # Parse statements inside union
        while not self.match(TokenType.RPAREN, TokenType.EOF):
            if self.match(TokenType.UNION_MINUS):
                # Difference operation
                self.advance()
                continue

            # Parse individual statement
            if not self.parse_statement():
                break

        self.expect(TokenType.RPAREN)

        # Handle output assignment
        if self.match(TokenType.ASSIGN):
            self.advance()
            if not self.match(TokenType.DOT):
                self.error("Expected '.' after '->' in union assignment")
            else:
                self.advance()
                if not self.match(TokenType.IDENTIFIER):
                    self.error("Expected set name after '.'")
                else:
                    self.advance()

        self.expect(TokenType.SEMICOLON)
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
                # Parse evaluator expression (simplified)
                while not self.match(TokenType.RPAREN, TokenType.EOF):
                    self.advance()
                self.expect(TokenType.RPAREN)

    def _parse_block_body(self) -> bool:
        """Parse block body and return whether braces were used."""
        has_braces = False
        if self.match(TokenType.LBRACE):
            has_braces = True
            self.advance()

            while not self.match(TokenType.RBRACE, TokenType.EOF):
                if not self.parse_statement():
                    break

            self.expect(TokenType.RBRACE)
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

        # Only expect semicolon if we didn't use braces
        if not has_braces:
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
        """Parse set reference (.setname;)."""
        if self.match(TokenType.DOT):
            self.advance()
            if not self.match(TokenType.IDENTIFIER):
                self.error("Expected set name after '.'")
            else:
                self.advance()

            self.expect(TokenType.SEMICOLON)
            return True
        return False

    def parse_simple_statement(self):
        """Parse simple statements like recursion operators, is_in, etc."""
        # Handle template placeholders as standalone statements
        if self.match(TokenType.TEMPLATE_PLACEHOLDER):
            self.advance()

            # Check if template placeholder is followed by tag filters (like
            # geocodeArea)
            while self.match(TokenType.LBRACKET):
                self.parse_tag_filter()

            # Optional assignment operator
            if self.match(TokenType.ASSIGN):
                self.advance()
                if self.match(TokenType.DOT):
                    self.advance()
                    if self.match(TokenType.IDENTIFIER):
                        self.advance()
            self.expect(TokenType.SEMICOLON)
            return True

        # Handle make statements
        if self.match(TokenType.MAKE):
            self._parse_make_statement()
            return True

        # Try different statement types
        if self._parse_recursion_statement():
            return True
        elif self._parse_is_in_statement():
            return True
        elif self._parse_set_reference():
            return True

        return False

    def _parse_make_statement(self) -> None:
        """Parse make statement: make identifier ,key=value,...;"""
        self.advance()  # Skip 'make'

        # Parse identifier (can contain backslashes like stat_highway_\1)
        if not self.match(TokenType.IDENTIFIER):
            self.error("Expected identifier after 'make'")
            return
        self.advance()

        # Parse comma-separated key=value pairs
        while self.match(TokenType.COMMA):
            self.advance()  # Skip comma

            # Parse key
            if not self.match(TokenType.IDENTIFIER):
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

        self.expect(TokenType.SEMICOLON)

    def _parse_make_value_expression(self) -> None:
        """Parse value expression in make statement."""
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
        # Handle simple values
        elif self.match(TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING):
            self.advance()
        else:
            self.error("Expected value expression in make statement")

    def _parse_make_function_args(self) -> None:
        """Parse function arguments in make statement."""
        while True:
            # Parse argument (can be function call or simple value)
            if (
                self.match(TokenType.IDENTIFIER)
                and self.peek_ahead(1)
                and self.peek_ahead(1).type == TokenType.LPAREN
            ):
                self.advance()  # Function name
                self.expect(TokenType.LPAREN)
                if not self.match(TokenType.RPAREN):
                    self._parse_make_function_args()
                self.expect(TokenType.RPAREN)
            elif self.match(TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING):
                self.advance()
            else:
                break

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

    def parse_statement(self) -> bool:
        """Parse any statement."""
        # Skip any leading comments or newlines
        while self.match(TokenType.COMMENT, TokenType.NEWLINE):
            self.advance()

        if self.match(TokenType.EOF):
            return False

        # Try different statement types
        if self.parse_query_statement():
            return True
        elif self.parse_out_statement():
            return True
        elif self.parse_union_statement():
            return True
        elif self.parse_block_statement():
            return True
        elif self.parse_simple_statement():
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

        # Check if first statement is settings
        if (
            first_non_comment < len(self.tokens)
            and self.tokens[first_non_comment].type == TokenType.LBRACKET
        ):
            self.pos = first_non_comment
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

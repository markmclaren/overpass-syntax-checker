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

    # Regex and operators in filters
    REGEX_OP = "~"
    NOT_OP = "!"
    EQUALS = "="
    NOT_EQUALS = "!="

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
        return f"Token({
            self.type.value}, '{
            self.value}', {
            self.line}:{
                self.column})"


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

    def read_string(self, quote_char: str) -> str:
        """Read a string literal."""
        value = ""
        self.advance()  # Skip opening quote

        while self.peek() and self.peek() != quote_char:
            char = self.advance()
            if char == "\\":
                # Handle escape sequences
                next_char = self.advance()
                if next_char == "n":
                    value += "\n"
                elif next_char == "t":
                    value += "\t"
                elif next_char == "r":
                    value += "\r"
                elif next_char == "\\":
                    value += "\\"
                elif next_char == quote_char:
                    value += quote_char
                elif next_char and next_char.startswith("u"):
                    # Unicode escape sequence \uXXXX
                    unicode_digits = ""
                    for _ in range(4):
                        digit = self.advance()
                        if digit and digit in "0123456789abcdefABCDEF":
                            unicode_digits += digit
                        else:
                            self.error("Invalid unicode escape sequence")
                    value += chr(int(unicode_digits, 16))
                else:
                    value += next_char
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

        # Subsequent characters can be letters, digits, or underscores
        while self.peek() and (self.peek().isalnum() or self.peek() == "_"):
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

    def tokenize(self) -> List[Token]:
        """Tokenize the input text."""
        self.tokens = []

        while self.pos < len(self.text):
            start_line = self.line
            start_column = self.column

            char = self.peek()

            if not char:
                break

            # Skip whitespace
            if char in " \t\r":
                self.skip_whitespace()
                continue

            # Newlines
            elif char == "\n":
                self.advance()
                self.tokens.append(
                    Token(TokenType.NEWLINE, "\\n", start_line, start_column)
                )

            # Comments
            elif char == "/" and self.peek(1) in ["/", "*"]:
                comment_text = self.read_comment()
                self.tokens.append(
                    Token(TokenType.COMMENT, comment_text, start_line, start_column)
                )

            # String literals
            elif char in ['"', "'"]:
                string_value = self.read_string(char)
                self.tokens.append(
                    Token(TokenType.STRING, string_value, start_line, start_column)
                )

            # Numbers
            elif char.isdigit() or (
                char == "-" and self.peek(1) and self.peek(1).isdigit()
            ):
                number_value = self.read_number()
                self.tokens.append(
                    Token(TokenType.NUMBER, number_value, start_line, start_column)
                )

            # Identifiers and keywords
            elif char.isalpha() or char == "_":
                identifier = self.read_identifier()
                token_type = self.KEYWORDS.get(identifier.lower(), TokenType.IDENTIFIER)
                self.tokens.append(
                    Token(token_type, identifier, start_line, start_column)
                )

            # Two-character operators
            elif char == "-" and self.peek(1) == ">":
                self.advance()
                self.advance()
                self.tokens.append(
                    Token(TokenType.ASSIGN, "->", start_line, start_column)
                )

            elif char == "<" and self.peek(1) == "<":
                self.advance()
                self.advance()
                self.tokens.append(
                    Token(TokenType.RECURSE_UP_REL, "<<", start_line, start_column)
                )

            elif char == ">" and self.peek(1) == ">":
                self.advance()
                self.advance()
                self.tokens.append(
                    Token(TokenType.RECURSE_DOWN_REL, ">>", start_line, start_column)
                )

            elif char == "!" and self.peek(1) == "=":
                self.advance()
                self.advance()
                self.tokens.append(
                    Token(TokenType.NOT_EQUALS, "!=", start_line, start_column)
                )

            # Single-character tokens
            elif char == ";":
                self.advance()
                self.tokens.append(
                    Token(TokenType.SEMICOLON, ";", start_line, start_column)
                )

            elif char == ",":
                self.advance()
                self.tokens.append(
                    Token(TokenType.COMMA, ",", start_line, start_column)
                )

            elif char == ".":
                self.advance()
                self.tokens.append(Token(TokenType.DOT, ".", start_line, start_column))

            elif char == ":":
                self.advance()
                self.tokens.append(
                    Token(TokenType.COLON, ":", start_line, start_column)
                )

            elif char == "(":
                self.advance()
                self.tokens.append(
                    Token(TokenType.LPAREN, "(", start_line, start_column)
                )

            elif char == ")":
                self.advance()
                self.tokens.append(
                    Token(TokenType.RPAREN, ")", start_line, start_column)
                )

            elif char == "[":
                self.advance()
                self.tokens.append(
                    Token(TokenType.LBRACKET, "[", start_line, start_column)
                )

            elif char == "]":
                self.advance()
                self.tokens.append(
                    Token(TokenType.RBRACKET, "]", start_line, start_column)
                )

            elif char == "{":
                self.advance()
                self.tokens.append(
                    Token(TokenType.LBRACE, "{", start_line, start_column)
                )

            elif char == "}":
                self.advance()
                self.tokens.append(
                    Token(TokenType.RBRACE, "}", start_line, start_column)
                )

            elif char == "<":
                self.advance()
                self.tokens.append(
                    Token(TokenType.RECURSE_UP, "<", start_line, start_column)
                )

            elif char == ">":
                self.advance()
                self.tokens.append(
                    Token(TokenType.RECURSE_DOWN, ">", start_line, start_column)
                )

            elif char == "-":
                self.advance()
                self.tokens.append(
                    Token(TokenType.UNION_MINUS, "-", start_line, start_column)
                )

            elif char == "~":
                self.advance()
                self.tokens.append(
                    Token(TokenType.REGEX_OP, "~", start_line, start_column)
                )

            elif char == "!":
                self.advance()
                self.tokens.append(
                    Token(TokenType.NOT_OP, "!", start_line, start_column)
                )

            elif char == "=":
                self.advance()
                self.tokens.append(
                    Token(TokenType.EQUALS, "=", start_line, start_column)
                )

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
            error_msg = f"Syntax Error at line {
                    token.line}, column {
                    token.column}: {message}"
        else:
            current = self.current_token()
            error_msg = f"Syntax Error at line {
                current.line}, column {
                current.column}: {message}"
        self.errors.append(error_msg)

    def warning(self, message: str, token: Optional[Token] = None):
        """Add a warning message."""
        if token:
            warning_msg = f"Warning at line {
                    token.line}, column {
                    token.column}: {message}"
        else:
            current = self.current_token()
            warning_msg = f"Warning at line {
                    current.line}, column {
                    current.column}: {message}"
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
            self.error(
                f"Expected {
                    expected_type.value}, got {
                    token.type.value}"
            )
        else:
            self.advance()
        return token

    def match(self, *token_types: TokenType) -> bool:
        """Check if current token matches any of the given types."""
        return self.current_token().type in token_types

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
                    self.expect(TokenType.COLON)

                    if not self.match(TokenType.NUMBER):
                        self.error(
                            f"Expected number after {
                                setting_token.value}:"
                        )
                    else:
                        number = self.advance()
                        try:
                            value = int(number.value)
                            if value < 0:
                                self.error(
                                    f"{setting_token.value} must be non-negative"
                                )
                        except ValueError:
                            self.error(
                                f"Invalid number for {
                                    setting_token.value}: {
                                    number.value}"
                            )

                elif setting_name == "bbox":
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
                                            f"Latitude must be between -90 and "
                                            f"90: {coord_val}"
                                        )
                                else:  # longitude values
                                    if not -180 <= coord_val <= 180:
                                        self.error(
                                            f"Longitude must be between -180 and "
                                            f"180: {coord_val}"
                                        )
                            except ValueError:
                                self.error(
                                    f"Invalid coordinate: {
                                        coord.value}"
                                )

                elif setting_name in ["date", "diff", "adiff"]:
                    self.expect(TokenType.COLON)

                    if not self.match(TokenType.STRING):
                        self.error(
                            f"Expected date string after {
                                setting_token.value}:"
                        )
                    else:
                        date_str = self.advance()
                        # Basic ISO 8601 date format validation
                        if not re.match(
                            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", date_str.value
                        ):
                            self.error(
                                "Invalid date format. Expected YYYY-MM-DDTHH:MM:SSZ"
                            )

                else:
                    # Unknown setting
                    self.warning(f"Unknown setting: {setting_token.value}")

                    if self.match(TokenType.COLON):
                        self.advance()
                        # Skip the value
                        if self.match(
                            TokenType.STRING, TokenType.NUMBER, TokenType.IDENTIFIER
                        ):
                            self.advance()

            elif self.match(TokenType.OUT):
                # Handle 'out' keyword as setting
                self.advance()  # Skip 'out'
                self.expect(TokenType.COLON)

                if self.match(TokenType.IDENTIFIER):
                    format_token = self.advance()
                    if format_token.value.lower() not in self.OUTPUT_FORMATS:
                        self.error(
                            f"Invalid output format: {
                                format_token.value}"
                        )
                elif self.match(TokenType.STRING):
                    # Could be csv with parameters
                    self.advance()
                else:
                    self.error("Expected output format after 'out:'")

            else:
                self.error("Expected setting name in settings block")
                break

            self.expect(TokenType.RBRACKET)

        self.expect(TokenType.SEMICOLON)
        return True

    def parse_tag_filter(self):
        """Parse tag filter [key] or [key=value] or [key~regex]."""
        self.expect(TokenType.LBRACKET)

        # Handle negation
        if self.match(TokenType.NOT_OP):
            self.advance()

        # Parse key (can be string or identifier)
        if self.match(TokenType.STRING, TokenType.IDENTIFIER):
            self.advance()  # Skip key

            # Check for operator
            if self.match(TokenType.EQUALS, TokenType.NOT_EQUALS, TokenType.REGEX_OP):
                op_token = self.advance()

                # Parse value
                if self.match(TokenType.STRING, TokenType.IDENTIFIER, TokenType.NUMBER):
                    value_token = self.advance()

                    # For regex operator, validate regex
                    if op_token.type == TokenType.REGEX_OP:
                        try:
                            re.compile(value_token.value)
                        except re.error as e:
                            self.error(f"Invalid regex pattern: {e}")

                    # Check for case insensitive flag for regex
                    if op_token.type == TokenType.REGEX_OP and self.match(
                        TokenType.COMMA
                    ):
                        self.advance()  # Skip comma
                        if self.match(TokenType.IDENTIFIER):
                            flag = self.advance()
                            if flag.value.lower() != "i":
                                self.error(f"Invalid regex flag: {flag.value}")
                else:
                    self.error("Expected value after operator in tag filter")

        elif self.match(TokenType.REGEX_OP):
            # Pattern like [~"name-regex"~"value-regex"]
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
                if self.match(TokenType.COMMA):
                    self.advance()
                    if self.match(TokenType.IDENTIFIER):
                        flag = self.advance()
                        if flag.value.lower() != "i":
                            self.error(f"Invalid regex flag: {flag.value}")
        else:
            self.error("Expected key name in tag filter")

        self.expect(TokenType.RBRACKET)

    def parse_spatial_filter(self):
        """Parse spatial filter like (bbox) or (around:radius,lat,lng)."""
        self.expect(TokenType.LPAREN)

        if self.match(TokenType.IDENTIFIER, TokenType.AREA):
            filter_type = self.advance()

            if filter_type.value.lower() == "around":
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

                    # Parse at least one coordinate pair
                    for coord_idx in range(2):  # lat, lng
                        if coord_idx > 0:
                            self.expect(TokenType.COMMA)

                        if not self.match(TokenType.NUMBER):
                            self.error(
                                f"Expected {
                                    'latitude' if coord_idx == 0 else 'longitude'}"
                            )
                        else:
                            coord = self.advance()
                            try:
                                coord_val = float(coord.value)
                                if coord_idx == 0:  # latitude
                                    if not -90 <= coord_val <= 90:
                                        self.error(
                                            f"Latitude must be between -90 and "
                                            f"90: {coord_val}"
                                        )
                                else:  # longitude
                                    if not -180 <= coord_val <= 180:
                                        self.error(
                                            f"Longitude must be between -180 and "
                                            f"180: {coord_val}"
                                        )
                            except ValueError:
                                self.error(
                                    f"Invalid coordinate: {
                                        coord.value}"
                                )

                    # Check for additional coordinate pairs (linestring)
                    while self.match(TokenType.COMMA):
                        self.advance()
                        if self.match(TokenType.NUMBER):
                            self.advance()  # Additional coordinates
                        else:
                            break

            elif filter_type.value.lower() == "poly":
                self.expect(TokenType.COLON)
                if not self.match(TokenType.STRING):
                    self.error("Expected polygon coordinate string after 'poly:'")
                else:
                    poly_str = self.advance()
                    # Basic validation of polygon string format
                    coords = poly_str.value.split()
                    if len(coords) < 6 or len(coords) % 2 != 0:
                        self.error("Polygon must have at least 3 coordinate pairs")

            elif filter_type.value.lower() == "area":
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

            else:
                # Could be other identifier-based filters
                filter_name = filter_type.value.lower()

                # Handle member filters (w, r, bn, bw, br)
                if filter_name in {"w", "r", "bn", "bw", "br"}:
                    # Handle optional .setname and :role
                    if self.match(TokenType.DOT):
                        self.advance()
                        if self.match(TokenType.IDENTIFIER):
                            self.advance()
                    if self.match(TokenType.COLON):
                        self.advance()
                        if self.match(TokenType.STRING):
                            self.advance()
                # Handle other filters with parameters
                elif self.match(TokenType.COLON):
                    self.advance()
                    if self.match(
                        TokenType.STRING, TokenType.NUMBER, TokenType.IDENTIFIER
                    ):
                        self.advance()

        # Could also be bbox coordinates or ID list
        elif self.match(TokenType.NUMBER):
            # Could be bbox (4 coordinates) or ID list or single ID
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
                    # Validate bbox coordinates
                    if not (-90 <= numbers[0] <= 90):  # south
                        self.error(
                            f"South latitude must be between -90 and 90: {numbers[0]}"
                        )
                    if not (-180 <= numbers[1] <= 180):  # west
                        self.error(
                            f"West longitude must be between -180 and 180: {numbers[1]}"
                        )
                    if not (-90 <= numbers[2] <= 90):  # north
                        self.error(
                            f"North latitude must be between -90 and 90: {numbers[2]}"
                        )
                    if not (-180 <= numbers[3] <= 180):  # east
                        self.error(
                            f"East longitude must be between -180 and 180: {numbers[3]}"
                        )
            except ValueError as e:
                self.error(f"Invalid coordinate value: {e}")

        # Handle special filter formats like id:123,456
        elif self.match(TokenType.IDENTIFIER):
            filter_name = self.advance()

            if self.match(TokenType.COLON):
                self.advance()  # Skip :

                if filter_name.value.lower() == "id":
                    # Parse ID list
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
                else:
                    # Other filters like newer:"date", user:"name", uid:123
                    if self.match(
                        TokenType.STRING, TokenType.NUMBER, TokenType.IDENTIFIER
                    ):
                        self.advance()

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

    def parse_out_statement(self):
        """Parse out statement."""
        if not self.match(TokenType.OUT):
            return False

        out_token = self.advance()

        # Handle input set prefix
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

        # Parse out parameters
        mode_specified = False
        while not self.match(TokenType.SEMICOLON, TokenType.EOF):
            if self.match(TokenType.IDENTIFIER):
                param = self.advance()
                param_lower = param.value.lower()

                if param_lower in self.OUT_MODES:
                    if mode_specified:
                        self.error("Multiple output modes specified")
                    mode_specified = True
                elif param_lower in self.OUT_MODIFIERS:
                    pass  # Valid modifier
                elif param_lower == "count":
                    # Special case for 'out count'
                    break
                else:
                    # Don't warn about unknown parameters, might be valid
                    # extensions
                    pass

            elif self.match(TokenType.NUMBER):
                # Limit parameter
                limit = self.advance()
                try:
                    limit_val = int(limit.value)
                    if limit_val < 0:
                        self.error("Output limit must be non-negative")
                except ValueError:
                    self.error(f"Invalid output limit: {limit.value}")

            elif self.match(TokenType.LPAREN):
                # Bounding box in out statement
                self.parse_spatial_filter()

            else:
                break

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
        if self.match(TokenType.DOT):
            # Input set
            self.advance()
            if not self.match(TokenType.IDENTIFIER):
                self.error("Expected set name after '.'")
            else:
                self.advance()

        if self.match(TokenType.ASSIGN):
            # Output set
            self.advance()
            if not self.match(TokenType.DOT):
                self.error("Expected '.' after '->'")
            else:
                self.advance()
                if not self.match(TokenType.IDENTIFIER):
                    self.error("Expected set name after '.'")
                else:
                    self.advance()

        # Parse parameters for specific block types
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

        # Parse block body
        if self.match(TokenType.LBRACE):
            self.advance()

            while not self.match(TokenType.RBRACE, TokenType.EOF):
                if not self.parse_statement():
                    break

            self.expect(TokenType.RBRACE)

        # Handle else clause for if statements
        if block_type.type == TokenType.IF and self.match(TokenType.ELSE):
            self.advance()
            if self.match(TokenType.LBRACE):
                self.advance()
                while not self.match(TokenType.RBRACE, TokenType.EOF):
                    if not self.parse_statement():
                        break
                self.expect(TokenType.RBRACE)

        if not self.match(
            TokenType.RBRACE
        ):  # Only expect semicolon if not ending with }
            self.expect(TokenType.SEMICOLON)

        return True

    def parse_simple_statement(self):
        """Parse simple statements like recursion operators, is_in, etc."""
        # Recursion operators
        if self.match(
            TokenType.RECURSE_UP,
            TokenType.RECURSE_UP_REL,
            TokenType.RECURSE_DOWN,
            TokenType.RECURSE_DOWN_REL,
        ):
            self.advance()  # Skip recursion operator

            # Handle input set
            if self.match(TokenType.DOT):
                self.advance()
                if not self.match(TokenType.IDENTIFIER):
                    self.error("Expected set name after '.'")
                else:
                    self.advance()

            # Handle output assignment
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

            self.expect(TokenType.SEMICOLON)
            return True

        # is_in statement
        elif self.match(TokenType.IS_IN):
            self.advance()

            # Handle coordinates
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

            # Handle output assignment
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

            self.expect(TokenType.SEMICOLON)
            return True

        # Set reference (.setname;)
        elif self.match(TokenType.DOT):
            self.advance()
            if not self.match(TokenType.IDENTIFIER):
                self.error("Expected set name after '.'")
            else:
                self.advance()

            self.expect(TokenType.SEMICOLON)
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
                f"Query validation result: {
                    'VALID' if result['valid'] else 'INVALID'}"
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

"""
Test cases for the CLI module.
"""

import os
import sys
import tempfile
from io import StringIO
from unittest.mock import patch

from src.overpass_ql_checker.cli import main


class TestCLI:
    """Test cases for the command-line interface."""

    def test_cli_with_valid_query(self):
        """Test CLI with a valid query string."""
        test_args = ["overpass-ql-check", "node[amenity=restaurant];out;"]

        with patch.object(sys, "argv", test_args):
            with patch.object(sys, "exit") as mock_exit:
                main()
                mock_exit.assert_called_with(0)

    def test_cli_with_invalid_query(self):
        """Test CLI with an invalid query string."""
        test_args = ["overpass-ql-check", "invalid query syntax"]

        with patch.object(sys, "argv", test_args):
            with patch.object(sys, "exit") as mock_exit:
                main()
                mock_exit.assert_called_with(1)

    def test_cli_with_verbose_flag(self):
        """Test CLI with verbose flag."""
        test_args = ["overpass-ql-check", "-v", "node[amenity=restaurant];out;"]

        with patch.object(sys, "argv", test_args):
            with patch.object(sys, "exit") as mock_exit:
                with patch("sys.stdout", new=StringIO()) as fake_out:
                    main()
                    mock_exit.assert_called_with(0)
                    output = fake_out.getvalue()
                    assert "VALID" in output
                    assert "TOKENS" in output

    def test_cli_with_file_input(self):
        """Test CLI with file input."""
        # Create a temporary file with a valid query
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".overpass", delete=False
        ) as f:
            f.write("node[amenity=restaurant];out;")
            temp_file = f.name

        try:
            test_args = ["overpass-ql-check", "-f", temp_file]

            with patch.object(sys, "argv", test_args):
                with patch.object(sys, "exit") as mock_exit:
                    main()
                    mock_exit.assert_called_with(0)
        finally:
            # Clean up the temporary file
            os.unlink(temp_file)

    def test_cli_with_nonexistent_file(self):
        """Test CLI with nonexistent file."""
        test_args = ["overpass-ql-check", "-f", "nonexistent_file.overpass"]

        with patch.object(sys, "argv", test_args):
            with patch.object(sys, "exit") as mock_exit:
                with patch("sys.stdout", new=StringIO()) as fake_out:
                    main()
                    mock_exit.assert_called_with(1)
                    output = fake_out.getvalue()
                    assert "Error: File" in output
                    assert "not found" in output

    def test_cli_with_no_arguments(self):
        """Test CLI with no arguments."""
        test_args = ["overpass-ql-check"]

        with patch.object(sys, "argv", test_args):
            with patch.object(sys, "exit") as mock_exit:
                with patch("sys.stdout", new=StringIO()) as fake_out:
                    main()
                    mock_exit.assert_called_with(1)
                    output = fake_out.getvalue()
                    assert "Error: Please provide a query string or file" in output

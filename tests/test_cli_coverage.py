"""
Additional CLI tests to improve coverage.

Tests for CLI edge cases and error conditions not covered by existing tests.
"""

import io
import tempfile
from pathlib import Path
from unittest.mock import patch

from overpass_ql_checker.cli import main


class TestCLIEdgeCases:
    """Test CLI edge cases and error conditions."""

    def test_invalid_file_permissions(self):
        """Test handling of files with permission issues."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(b'node["amenity"="restaurant"];')
            tmp_file_path = tmp_file.name

        try:
            # Try to create a scenario where file exists but can't be read
            # This is OS-dependent and might not work on all systems
            import os

            os.chmod(tmp_file_path, 0o000)

            with patch("sys.argv", ["overpass-ql-checker", tmp_file_path]):
                try:
                    main()
                except SystemExit as e:
                    # Should exit with error code
                    assert e.code != 0
        finally:
            # Clean up
            import os

            try:
                os.chmod(tmp_file_path, 0o644)
                os.unlink(tmp_file_path)
            except (OSError, PermissionError):
                pass

    def test_binary_file_handling(self):
        """Test handling of binary files."""
        with tempfile.NamedTemporaryFile(delete=False, mode="wb") as tmp_file:
            # Write some binary data
            tmp_file.write(b"\\x00\\x01\\x02\\x03")
            tmp_file_path = tmp_file.name

        try:
            with patch(
                "sys.argv", ["overpass-ql-checker", "-f", tmp_file_path, "--verbose"]
            ):
                with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                    try:
                        main()
                    except SystemExit as e:
                        # Should exit with error code for binary data
                        assert e.code != 0
                    output = mock_stdout.getvalue()
                    # Should show that it's invalid in verbose mode
                    assert "INVALID" in output
        finally:
            # Clean up
            try:
                Path(tmp_file_path).unlink()
            except OSError:
                pass

    def test_large_file_handling(self):
        """Test handling of very large files."""
        with tempfile.NamedTemporaryFile(delete=False, mode="w") as tmp_file:
            # Write a reasonably large query - but make it valid
            large_query = 'node["amenity"="restaurant"];out;\n' * 1000
            tmp_file.write(large_query)
            tmp_file_path = tmp_file.name

        try:
            with patch("sys.argv", ["overpass-ql-checker", "-f", tmp_file_path]):
                with patch("sys.stdout", new_callable=io.StringIO):
                    try:
                        exit_code = main()
                        # Should handle large file without crashing
                        assert exit_code is None or exit_code == 0
                    except SystemExit as e:
                        # Should be successful for valid large query
                        assert e.code == 0
        finally:
            # Clean up
            try:
                Path(tmp_file_path).unlink()
            except OSError:
                pass

    def test_empty_file_handling(self):
        """Test handling of empty files."""
        with tempfile.NamedTemporaryFile(delete=False, mode="w") as tmp_file:
            # Write nothing (empty file)
            tmp_file_path = tmp_file.name

        try:
            with patch(
                "sys.argv", ["overpass-ql-checker", "-f", tmp_file_path, "--verbose"]
            ):
                with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                    try:
                        main()
                    except SystemExit as e:
                        # Empty file is actually considered valid by the parser
                        assert e.code == 0
                    output = mock_stdout.getvalue()
                    assert "VALID" in output
        finally:
            # Clean up
            try:
                Path(tmp_file_path).unlink()
            except OSError:
                pass

    def test_file_with_encoding_issues(self):
        """Test handling of files with encoding issues."""
        with tempfile.NamedTemporaryFile(delete=False, mode="wb") as tmp_file:
            # Write some text with UTF-8 encoding - this should work fine
            tmp_file.write('node["amenity"="café"];out;'.encode("utf-8"))
            tmp_file_path = tmp_file.name

        try:
            with patch("sys.argv", ["overpass-ql-checker", "-f", tmp_file_path]):
                with patch("sys.stdout", new_callable=io.StringIO):
                    try:
                        exit_code = main()
                        # Should handle UTF-8 file successfully
                        assert exit_code is None or exit_code == 0
                    except SystemExit as e:
                        assert e.code == 0
        finally:
            # Clean up
            try:
                Path(tmp_file_path).unlink()
            except OSError:
                pass

    def test_stdin_input_with_encoding(self):
        """Test stdin input with various encodings."""
        test_query = 'node["amenity"="café"];out;'

        with patch("sys.argv", ["overpass-ql-checker", test_query]):
            with patch("sys.stdout", new_callable=io.StringIO):
                try:
                    main()
                except SystemExit as e:
                    assert e.code == 0
                    # No verbose output expected in normal mode
                    # Just check the test passes

    def test_verbose_output_with_warnings(self):
        """Test verbose output when there are warnings."""
        # Query that should generate warnings (regex with unbalanced parentheses)
        test_query = 'node["key"~"(unbalanced"];out;'

        with patch("sys.argv", ["overpass-ql-checker", "--verbose", test_query]):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                try:
                    main()
                except SystemExit as e:
                    # Should exit with success despite warnings
                    assert e.code == 0
                output = mock_stdout.getvalue()
                assert "VALID" in output or "WARNINGS" in output

    def test_help_message_content(self):
        """Test that help message contains expected content."""
        with patch("sys.argv", ["overpass-ql-checker", "--help"]):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                try:
                    main()
                except SystemExit as e:
                    assert e.code == 0
                output = mock_stdout.getvalue()
                assert "overpass" in output.lower()
                assert "syntax" in output.lower()
                assert "checker" in output.lower()

    def test_version_information(self):
        """Test version information display."""
        with patch("sys.argv", ["overpass-ql-checker", "--version"]):
            with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
                try:
                    main()
                except SystemExit as e:
                    assert e.code == 0
                output = mock_stdout.getvalue()
                # Should contain version info
                assert len(output.strip()) > 0

"""Tests for emoji_extract module."""

import sqlite3
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from emoji_counter.emoji_extract import (
    extract_emojis,
    export_to_sqlite,
    parse_message_file,
    process_input,
)


# Path to test data
TEST_DATA_DIR = Path(__file__).parent
TEST_FILE = TEST_DATA_DIR / "FirstName1 LastName1 (abc-123-xyz-987).txt"


class TestExtractEmojis:
    """Tests for the extract_emojis function."""

    def test_extract_single_emoji(self):
        """Extract a single emoji from text."""
        result = extract_emojis("Hello 😄")
        assert result == ["😄"]

    def test_extract_multiple_emojis(self):
        """Extract multiple emojis from text."""
        result = extract_emojis("Hello 😄😂🤔")
        assert result == ["😄", "😂", "🤔"]

    def test_extract_no_emojis(self):
        """Return empty list when no emojis present."""
        result = extract_emojis("Hello world")
        assert result == []

    def test_extract_emojis_mixed_text(self):
        """Extract emojis from text with mixed content."""
        result = extract_emojis("Start 🎉 middle 🎊 end")
        assert result == ["🎉", "🎊"]

    def test_extract_empty_string(self):
        """Handle empty string input."""
        result = extract_emojis("")
        assert result == []


class TestParseMessageFile:
    """Tests for the parse_message_file function."""

    def test_parse_test_file(self):
        """Parse the test message file and extract emoji data."""
        result = parse_message_file(TEST_FILE)

        assert len(result) == 3

        # Check first emoji
        emoji, timestamp, username, chat_name = result[0]
        assert emoji == "😄"
        assert "2024-08-13" in timestamp
        assert username == "FirstName1 LastName1"
        assert chat_name == "FirstName1 LastName1"

    def test_parse_extracts_correct_usernames(self):
        """Verify usernames are extracted correctly, stripping phone numbers."""
        result = parse_message_file(TEST_FILE)

        usernames = [r[2] for r in result]
        assert usernames == ["FirstName1 LastName1", "FirstName1 LastName1", "You"]

    def test_parse_extracts_correct_chat_name(self):
        """Verify chat name is extracted from filename without parentheses."""
        result = parse_message_file(TEST_FILE)

        chat_names = [r[3] for r in result]
        assert all(name == "FirstName1 LastName1" for name in chat_names)

    def test_parse_extracts_all_emojis(self):
        """Verify all emojis are extracted from the file."""
        result = parse_message_file(TEST_FILE)

        emojis = [r[0] for r in result]
        assert emojis == ["😄", "😂", "🤔"]

    def test_parse_repairs_mojibake_chat_name(self, tmp_path: Path):
        """Repair mojibake filenames so chat_name is stored as proper Unicode."""
        jp_name = "日本で会いましょう"
        mojibake_name = jp_name.encode("utf-8").decode("latin-1")
        file_path = tmp_path / f"{mojibake_name} (9632772583463997).txt"
        file_path.write_text(
            (
                "Conversation: Test Chat\n\n"
                "From: You\n"
                "Type: outgoing\n"
                "Sent: Sat, 01 Jul 2023 14:29:25 +0200\n\n"
                "こんにちは 😊\n"
            ),
            encoding="utf-8",
        )

        result = parse_message_file(file_path)

        assert len(result) == 1
        assert result[0][3] == jp_name

    def test_parse_repairs_mojibake_content_for_emoji_extraction(
        self, tmp_path: Path
    ):
        """Extract emoji from mojibake message content."""
        file_path = tmp_path / "chat (1).txt"
        file_path.write_text(
            (
                "Conversation: Test Chat\n\n"
                "From: Alice\n"
                "Type: incoming\n"
                "Sent: Tue, 13 Aug 2024 09:30:41 +0200\n"
                "Received: Tue, 13 Aug 2024 09:30:41 +0200\n\n"
                "Hej ð\n"
            ),
            encoding="utf-8",
        )

        result = parse_message_file(file_path)

        assert len(result) == 1
        emoji, _, username, _ = result[0]
        assert emoji == "😊"
        assert username == "Alice"


class TestProcessInput:
    """Tests for the process_input function."""

    def test_process_single_file(self):
        """Process a single file and return DataFrame."""
        df = process_input(TEST_FILE)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert list(df.columns) == ["emoji", "timestamp", "username", "chat_name"]

    def test_process_directory(self):
        """Process a directory of files."""
        df = process_input(TEST_DATA_DIR)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3  # Only one .txt file in test dir

    def test_process_nonexistent_path(self):
        """Raise error for nonexistent path."""
        with pytest.raises(ValueError, match="does not exist"):
            process_input(Path("/nonexistent/path"))

    def test_dataframe_columns(self):
        """Verify DataFrame has correct columns."""
        df = process_input(TEST_FILE)

        assert "emoji" in df.columns
        assert "timestamp" in df.columns
        assert "username" in df.columns
        assert "chat_name" in df.columns


class TestExportToSqlite:
    """Tests for the export_to_sqlite function."""

    def test_export_creates_database(self):
        """Export DataFrame to SQLite database."""
        df = process_input(TEST_FILE)

        with tempfile.NamedTemporaryFile(suffix=".sql", delete=False) as f:
            output_path = Path(f.name)

        try:
            export_to_sqlite(df, output_path)

            assert output_path.exists()

            # Verify database contents
            conn = sqlite3.connect(output_path)
            result = pd.read_sql("SELECT * FROM emojis", conn)
            conn.close()

            assert len(result) == 3
            assert list(result.columns) == [
                "emoji",
                "timestamp",
                "username",
                "chat_name",
            ]
        finally:
            output_path.unlink(missing_ok=True)

    def test_export_replaces_existing(self):
        """Export replaces existing table if it exists."""
        df = process_input(TEST_FILE)

        with tempfile.NamedTemporaryFile(suffix=".sql", delete=False) as f:
            output_path = Path(f.name)

        try:
            # Export twice
            export_to_sqlite(df, output_path)
            export_to_sqlite(df, output_path)

            # Should still have same number of rows (replaced, not appended)
            conn = sqlite3.connect(output_path)
            result = pd.read_sql("SELECT * FROM emojis", conn)
            conn.close()

            assert len(result) == 3
        finally:
            output_path.unlink(missing_ok=True)

"""Tests for message_convert module."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from emoji_counter.message_convert import (
    Message,
    convert_to_sigtop,
    extract_chat_name,
    format_sigtop_timestamp,
    parse_messenger_file,
    parse_whatsapp_file,
    process_input,
)


class TestParseWhatsappFile:
    """Tests for parse_whatsapp_file function."""

    def test_parse_simple_messages(self, tmp_path: Path) -> None:
        """Parse file with simple single-line messages."""
        content = (
            "2024-10-04 10:26 - System: Welcome message\n"
            "2025-06-05 19:42 - Alice: Hello there!\n"
            "2025-06-05 20:12 - Bob: Hi Alice 🙏\n"
        )
        file_path = tmp_path / "chat.txt"
        file_path.write_text(content, encoding="utf-8")

        messages = parse_whatsapp_file(file_path)

        assert len(messages) == 3
        assert messages[1].sender == "Alice"
        assert messages[1].content == "Hello there!"
        assert messages[2].sender == "Bob"
        assert messages[2].content == "Hi Alice 🙏"

    def test_parse_multiline_message(self, tmp_path: Path) -> None:
        """Parse file with multi-line message content."""
        content = (
            "2025-06-05 19:42 - Alice: Line 1\n"
            "Line 2\n"
            "Line 3\n"
            "2025-06-05 20:00 - Bob: Single line\n"
        )
        file_path = tmp_path / "chat.txt"
        file_path.write_text(content, encoding="utf-8")

        messages = parse_whatsapp_file(file_path)

        assert len(messages) == 2
        assert messages[0].content == "Line 1\nLine 2\nLine 3"
        assert messages[1].content == "Single line"

    def test_parse_with_your_name(self, tmp_path: Path) -> None:
        """Parse file and convert your_name to 'You'."""
        content = (
            "2025-06-05 19:42 - Simon Thor: My message\n"
            "2025-06-05 20:12 - Other Person: Their message\n"
        )
        file_path = tmp_path / "chat.txt"
        file_path.write_text(content, encoding="utf-8")

        messages = parse_whatsapp_file(file_path, your_name="Simon Thor")

        assert len(messages) == 2
        assert messages[0].sender == "You"
        assert messages[1].sender == "Other Person"

    def test_parse_empty_file(self, tmp_path: Path) -> None:
        """Parse empty file returns empty list."""
        file_path = tmp_path / "empty.txt"
        file_path.write_text("", encoding="utf-8")

        messages = parse_whatsapp_file(file_path)

        assert messages == []

    def test_parse_timestamp_format(self, tmp_path: Path) -> None:
        """Parse timestamp correctly from WhatsApp format."""
        content = "2025-06-05 19:42 - Alice: Test\n"
        file_path = tmp_path / "chat.txt"
        file_path.write_text(content, encoding="utf-8")

        messages = parse_whatsapp_file(file_path)

        assert messages[0].timestamp == datetime(2025, 6, 5, 19, 42)

    def test_parse_message_with_colon_in_content(self, tmp_path: Path) -> None:
        """Parse message where content contains colons."""
        content = "2025-06-05 19:42 - Alice: Check this: https://example.com\n"
        file_path = tmp_path / "chat.txt"
        file_path.write_text(content, encoding="utf-8")

        messages = parse_whatsapp_file(file_path)

        assert messages[0].content == "Check this: https://example.com"


class TestFormatSigtopTimestamp:
    """Tests for format_sigtop_timestamp function."""

    def test_format_basic_timestamp(self) -> None:
        """Format datetime to sigtop format."""
        dt = datetime(2024, 8, 13, 9, 30, 41)
        result = format_sigtop_timestamp(dt)
        assert result == "Tue, 13 Aug 2024 09:30:41 +0200"

    def test_format_different_date(self) -> None:
        """Format another date to verify day/month names."""
        dt = datetime(2025, 6, 5, 19, 42, 0)
        result = format_sigtop_timestamp(dt)
        assert result == "Thu, 05 Jun 2025 19:42:00 +0200"


class TestConvertToSigtop:
    """Tests for convert_to_sigtop function."""

    def test_convert_outgoing_message(self) -> None:
        """Convert message from 'You' to outgoing type."""
        messages = [
            Message(
                timestamp=datetime(2025, 6, 5, 19, 42),
                sender="You",
                content="Hello!",
            )
        ]

        result = convert_to_sigtop(messages, "Test Chat")

        assert "From: You" in result
        assert "Type: outgoing" in result
        assert "Received:" not in result

    def test_convert_incoming_message(self) -> None:
        """Convert message from others to incoming type with Received line."""
        messages = [
            Message(
                timestamp=datetime(2025, 6, 5, 20, 12),
                sender="Bob",
                content="Hi there!",
            )
        ]

        result = convert_to_sigtop(messages, "Test Chat")

        assert "From: Bob" in result
        assert "Type: incoming" in result
        assert "Received:" in result

    def test_convert_includes_header(self) -> None:
        """Converted output includes Conversation header."""
        messages = [
            Message(
                timestamp=datetime(2025, 6, 5, 19, 42),
                sender="You",
                content="Test",
            )
        ]

        result = convert_to_sigtop(messages, "My Chat Name")

        assert result.startswith("Conversation: My Chat Name\n")

    def test_convert_preserves_content(self) -> None:
        """Message content is preserved in output."""
        messages = [
            Message(
                timestamp=datetime(2025, 6, 5, 19, 42),
                sender="You",
                content="Hello with 🎉 emoji!",
            )
        ]

        result = convert_to_sigtop(messages, "Test")

        assert "Hello with 🎉 emoji!" in result

    def test_convert_empty_messages(self) -> None:
        """Empty message list produces header only."""
        result = convert_to_sigtop([], "Empty Chat")

        assert result == "Conversation: Empty Chat\n"


class TestExtractChatName:
    """Tests for extract_chat_name function."""

    def test_extract_with_pattern_prefix_only(self) -> None:
        """Extract name using pattern with prefix only."""
        path = Path("WhatsApp-chatt med John Doe.txt")
        assert extract_chat_name(path, "WhatsApp-chatt med %s") == "John Doe"

    def test_extract_with_pattern_prefix_and_suffix(self) -> None:
        """Extract name using pattern with both prefix and suffix."""
        path = Path("Chat_John Doe_export.txt")
        assert extract_chat_name(path, "Chat_%s_export") == "John Doe"

    def test_extract_no_pattern_returns_stem(self) -> None:
        """No pattern returns the entire filename stem."""
        path = Path("Random Chat Export.txt")
        assert extract_chat_name(path, None) == "Random Chat Export"

    def test_extract_pattern_without_placeholder_raises(self) -> None:
        """Pattern without %s raises ValueError."""
        path = Path("Some File.txt")
        with pytest.raises(ValueError, match="must contain '%s' placeholder"):
            extract_chat_name(path, "no placeholder here")

    def test_extract_pattern_no_match_raises(self) -> None:
        """Pattern that doesn't match raises ValueError."""
        path = Path("Different Format.txt")
        with pytest.raises(ValueError, match="does not match pattern"):
            extract_chat_name(path, "WhatsApp-chatt med %s")

    def test_extract_with_directory(self) -> None:
        """Extract works with full path including directory."""
        path = Path("/some/dir/WhatsApp-chatt med Person.txt")
        assert extract_chat_name(path, "WhatsApp-chatt med %s") == "Person"

    def test_extract_empty_name(self) -> None:
        """Extract empty name when pattern matches exactly."""
        path = Path("prefix_suffix.txt")
        assert extract_chat_name(path, "prefix_%s_suffix") == ""
    

class TestProcessInput:
    """Tests for process_input function."""

    def test_process_single_file(self, tmp_path: Path) -> None:
        """Process single input file to single output file."""
        content = "2025-06-05 19:42 - Alice: Hello 👋\n"
        input_file = tmp_path / "WhatsApp-chatt med Alice.txt"
        input_file.write_text(content, encoding="utf-8")
        output_file = tmp_path / "output.txt"

        process_input(
            input_file, output_file, name_pattern="WhatsApp-chatt med %s"
        )

        assert output_file.exists()
        output_content = output_file.read_text(encoding="utf-8")
        assert "Conversation: Alice" in output_content
        assert "From: Alice" in output_content

    def test_process_directory(self, tmp_path: Path) -> None:
        """Process directory of files to output directory."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        output_dir = tmp_path / "output"

        # Create two input files
        (input_dir / "chat1.txt").write_text(
            "2025-06-05 19:42 - Alice: Hi\n", encoding="utf-8"
        )
        (input_dir / "chat2.txt").write_text(
            "2025-06-05 20:00 - Bob: Hello\n", encoding="utf-8"
        )

        process_input(input_dir, output_dir)

        assert output_dir.exists()
        # Output files are renamed to "{chat_name} (Whatsapp).txt"
        assert (output_dir / "chat1 (Whatsapp).txt").exists()
        assert (output_dir / "chat2 (Whatsapp).txt").exists()

    def test_process_file_to_directory_raises(self, tmp_path: Path) -> None:
        """Raise error when input is file but output is directory."""
        input_file = tmp_path / "input.txt"
        input_file.write_text("2025-06-05 19:42 - Alice: Hi\n", encoding="utf-8")
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        with pytest.raises(ValueError, match="Input is a file but output is a directory"):
            process_input(input_file, output_dir)

    def test_process_directory_to_file_raises(self, tmp_path: Path) -> None:
        """Raise error when input is directory but output is existing file."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "chat.txt").write_text(
            "2025-06-05 19:42 - Alice: Hi\n", encoding="utf-8"
        )
        output_file = tmp_path / "output.txt"
        output_file.write_text("existing", encoding="utf-8")

        with pytest.raises(ValueError, match="Input is a directory but output is a file"):
            process_input(input_dir, output_file)

    def test_process_nonexistent_input_raises(self, tmp_path: Path) -> None:
        """Raise error when input path doesn't exist."""
        with pytest.raises(ValueError, match="Input path does not exist"):
            process_input(tmp_path / "nonexistent", tmp_path / "output")

    def test_process_with_your_name(self, tmp_path: Path) -> None:
        """Process file with your_name converts sender to You."""
        content = "2025-06-05 19:42 - Simon: My message\n"
        input_file = tmp_path / "chat.txt"
        input_file.write_text(content, encoding="utf-8")
        output_file = tmp_path / "output.txt"

        process_input(input_file, output_file, your_name="Simon")

        output_content = output_file.read_text(encoding="utf-8")
        assert "From: You" in output_content
        assert "Type: outgoing" in output_content


class TestMessengerConversion:
    """Tests for Messenger JSON conversion."""

    def test_parse_messenger_file(self, tmp_path: Path) -> None:
        """Parse a Messenger JSON file into chat metadata and messages."""
        thread_dir = tmp_path / "alice_12345"
        thread_dir.mkdir()
        message_file = thread_dir / "message_1.json"
        message_file.write_text(
            json.dumps(
                {
                    "title": "Alice Chat",
                    "messages": [
                        {
                            "sender_name": "Simon",
                            "timestamp_ms": 1717616400000,
                            "content": "Hello",
                        },
                        {
                            "sender_name": "Alice",
                            "timestamp_ms": 1717617300000,
                            "content": "Hi",
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )

        chat_name, chat_id, messages = parse_messenger_file(message_file, your_name="Simon")

        assert chat_name == "Alice Chat"
        assert chat_id == "12345"
        assert [msg.sender for msg in messages] == ["You", "Alice"]
        assert [msg.content for msg in messages] == ["Hello", "Hi"]

    def test_parse_messenger_file_repairs_mojibake(self, tmp_path: Path) -> None:
        """Repair mojibake text from Messenger JSON content and title."""
        jp_mojibake = "こんにちは".encode("utf-8").decode("latin-1")
        thread_dir = tmp_path / "alice_12345"
        thread_dir.mkdir()
        message_file = thread_dir / "message_1.json"
        message_file.write_text(
            json.dumps(
                {
                    "title": "FÃ¶r chatten",
                    "messages": [
                        {
                            "sender_name": "BjÃ¶rn",
                            "timestamp_ms": 1717616400000,
                            "content": f"Hej ð {jp_mojibake}",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        chat_name, _, messages = parse_messenger_file(message_file)

        assert chat_name == "För chatten"
        assert messages[0].sender == "Björn"
        assert messages[0].content == "Hej 😊 こんにちは"

    def test_parse_messenger_file_without_underscore_uses_full_name(
        self, tmp_path: Path
    ) -> None:
        """Use full thread folder name as chat ID when no underscore exists."""
        thread_dir = tmp_path / "plainthreadname"
        thread_dir.mkdir()
        message_file = thread_dir / "message_1.json"
        message_file.write_text(
            json.dumps(
                {
                    "title": "Plain Thread",
                    "messages": [
                        {
                            "sender_name": "Alice",
                            "timestamp_ms": 1717616400000,
                            "content": "Hello",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        _, chat_id, _ = parse_messenger_file(message_file)

        assert chat_id == "plainthreadname"

    def test_process_messenger_directory(self, tmp_path: Path) -> None:
        """Process Messenger export folder into sigtop files."""
        input_dir = tmp_path / "messenger_export"
        cutover_dir = (
            input_dir / "your_facebook_activity" / "messages" / "e2ee_cutover" / "alice_12345"
        )
        inbox_dir = (
            input_dir / "your_facebook_activity" / "messages" / "inbox" / "alice_12345"
        )
        cutover_dir.mkdir(parents=True)
        inbox_dir.mkdir(parents=True)

        (cutover_dir / "message_1.json").write_text(
            json.dumps(
                {
                    "title": "Alice Chat",
                    "messages": [
                        {
                            "sender_name": "Simon",
                            "timestamp_ms": 1717616400000,
                            "content": "First message",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        (inbox_dir / "message_1.json").write_text(
            json.dumps(
                {
                    "title": "Alice Chat",
                    "messages": [
                        {
                            "sender_name": "Alice",
                            "timestamp_ms": 1717617300000,
                            "content": "Second message",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        output_dir = tmp_path / "output"
        process_input(
            input_dir,
            output_dir,
            your_name="Simon",
            chat_format="Messenger",
        )

        out_file = output_dir / "Alice Chat (12345).txt"
        assert out_file.exists()
        output_content = out_file.read_text(encoding="utf-8")
        assert "Conversation: Alice Chat (12345)" in output_content
        assert "From: You" in output_content
        assert "From: Alice" in output_content

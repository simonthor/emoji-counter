#!/usr/bin/env python3
"""
Convert chat exports from various formats to sigtop format for use with emoji-extract.

Supported formats:
- WhatsApp: ``YYYY-MM-DD HH:MM - Username: Message``

Sigtop output format: Multi-line blocks with ``From:``, ``Type:``, ``Sent:`` headers.
"""

import argparse
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

WHATSAPP_MSG_PATTERN = re.compile(
    r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}) - ([^:]+): (.*)$"
)
"""Regex pattern matching WhatsApp message lines."""


@dataclass
class Message:
    """Parsed chat message with timestamp, sender, and content."""

    timestamp: datetime
    """Message timestamp."""

    sender: str
    """Display name of the message sender."""

    content: str
    """Message text content."""


def parse_whatsapp_file(
    file_path: Path, your_name: str | None = None
) -> list[Message]:
    """Parse a WhatsApp chat export file into a list of messages.

    Handles multi-line messages by accumulating content until the next
    timestamp line. Skips system messages (lines without a sender).

    :param file_path: Path to the WhatsApp export text file.
    :param your_name: Your display name in WhatsApp. If provided, messages from
        this sender will be marked as "You" in the output.
    :returns: List of parsed messages in chronological order.
    """
    messages: list[Message] = []
    current_msg: Message | None = None

    with open(file_path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            match = WHATSAPP_MSG_PATTERN.match(line)

            if match:
                # Save previous message if exists
                if current_msg is not None:
                    messages.append(current_msg)

                timestamp_str, sender, content = match.groups()
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M")

                # Convert sender name to "You" if it matches your_name
                if your_name and sender == your_name:
                    sender = "You"

                current_msg = Message(
                    timestamp=timestamp,
                    sender=sender,
                    content=content,
                )
            elif current_msg is not None:
                # Continuation of previous message (multi-line)
                current_msg.content += "\n" + line

    # Don't forget the last message
    if current_msg is not None:
        messages.append(current_msg)

    return messages


def format_sigtop_timestamp(dt: datetime) -> str:
    """Format a datetime as sigtop-style timestamp.

    Produces format like ``Tue, 13 Aug 2024 09:30:41 +0200``.

    :param dt: Datetime to format.
    :returns: Formatted timestamp string with assumed +0200 timezone.
    """
    # WhatsApp exports don't include timezone, assume local (+0200)
    return dt.strftime("%a, %d %b %Y %H:%M:%S +0200")


def convert_to_sigtop(messages: list[Message], chat_name: str) -> str:
    """Convert parsed messages to sigtop format.

    Produces a complete sigtop-format document with conversation header
    and individual message blocks.

    :param messages: List of parsed messages.
    :param chat_name: Name to use in the ``Conversation:`` header.
    :returns: Complete sigtop-format text ready to write to file.
    """
    lines: list[str] = []

    # Header
    lines.append(f"Conversation: {chat_name}")
    lines.append("")

    for msg in messages:
        # Determine message type based on sender
        msg_type = "outgoing" if msg.sender == "You" else "incoming"

        lines.append(f"From: {msg.sender}")
        lines.append(f"Type: {msg_type}")
        lines.append(f"Sent: {format_sigtop_timestamp(msg.timestamp)}")

        # Add Received line for incoming messages (same as Sent for simplicity)
        if msg_type == "incoming":
            lines.append(f"Received: {format_sigtop_timestamp(msg.timestamp)}")

        lines.append("")
        lines.append(msg.content)
        lines.append("")

    return "\n".join(lines)


def extract_chat_name(file_path: Path, name_pattern: str | None = None) -> str:
    """Extract chat name from chat export filename using a pattern.

    Uses ``%s`` as placeholder for the chat name in the pattern. For example,
    pattern ``"WhatsApp-chatt med %s"`` matches ``"WhatsApp-chatt med John.txt"``
    and extracts ``"John"``.

    :param file_path: Path to the chat export file.
    :param name_pattern: Pattern with ``%s`` placeholder for the name. If ``None``,
        returns the entire filename stem.
    :returns: Extracted chat name.
    :raises ValueError: If pattern is provided but doesn't match the filename,
        or if pattern doesn't contain ``%s`` placeholder.
    """
    stem = file_path.stem

    if name_pattern is None:
        return stem

    # Split pattern on %s to get prefix and suffix
    if "%s" not in name_pattern:
        raise ValueError(f"Pattern '{name_pattern}' must contain '%s' placeholder")

    parts = name_pattern.split("%s", 1)
    prefix = parts[0]
    suffix = parts[1] if len(parts) > 1 else ""

    # Check if stem matches the pattern
    if stem.startswith(prefix) and stem.endswith(suffix):
        # Extract the name between prefix and suffix
        start = len(prefix)
        end = len(stem) - len(suffix) if suffix else len(stem)
        return stem[start:end]

    raise ValueError(
        f"Filename '{file_path.name}' does not match pattern '{name_pattern}'"
    )


def convert_file(
    input_path: Path,
    output_path: Path,
    your_name: str | None = None,
    name_pattern: str | None = None,
) -> None:
    """Convert a single chat export file to sigtop format.

    :param input_path: Path to input chat export file.
    :param output_path: Path where sigtop format output will be written.
    :param your_name: Your display name in the chat for sender identification.
    :param name_pattern: Pattern with ``%s`` for extracting chat name from filename.
    """
    chat_name = extract_chat_name(input_path, name_pattern)
    messages = parse_whatsapp_file(input_path, your_name)
    sigtop_content = convert_to_sigtop(messages, chat_name)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(sigtop_content)

    print(f"Converted: {input_path} -> {output_path}")


def process_input(
    input_path: Path,
    output_path: Path,
    your_name: str | None = None,
    name_pattern: str | None = None,
) -> None:
    """Process input file or folder and write converted output.

    If input is a file, output must be a file. If input is a directory,
    output must be a directory. All ``.txt`` files in input directory
    are converted.

    :param input_path: Path to input file or directory.
    :param output_path: Path to output file or directory.
    :param your_name: Your display name in the chat for sender identification.
    :param name_pattern: Pattern with ``%s`` for extracting chat name from filename.
    :raises ValueError: If input/output path types don't match (file vs directory).
    """
    if input_path.is_file():
        if output_path.is_dir():
            raise ValueError(
                "Input is a file but output is a directory. "
                "Both must be files or both must be directories."
            )
        convert_file(input_path, output_path, your_name, name_pattern)

    elif input_path.is_dir():
        if output_path.exists() and output_path.is_file():
            raise ValueError(
                "Input is a directory but output is a file. "
                "Both must be files or both must be directories."
            )

        output_path.mkdir(parents=True, exist_ok=True)

        txt_files = list(input_path.glob("*.txt"))
        if not txt_files:
            print(f"No .txt files found in {input_path}")
            return

        for txt_file in txt_files:
            chat_name = extract_chat_name(txt_file, name_pattern)
            out_file = output_path / f"{chat_name} (Whatsapp).txt"
            convert_file(txt_file, out_file, your_name, name_pattern)

        print(f"Converted {len(txt_files)} files")

    else:
        raise ValueError(f"Input path does not exist: {input_path}")


def main() -> int | None:
    """Parse arguments and run the chat format conversion.

    :returns: Exit code ``1`` on error, ``None`` on success.
    """
    parser = argparse.ArgumentParser(
        description="Convert chat exports to sigtop format"
    )
    parser.add_argument(
        "-i",
        "--input",
        type=str,
        required=True,
        help="Input file or folder containing chat exports",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        required=True,
        help="Output file or folder for sigtop format files",
    )
    parser.add_argument(
        "--your-name",
        type=str,
        default=None,
        help="Your display name in the chat (messages from this sender become 'You'). If not specified, the whole file name except for the extension is used as the chat name.",
    )
    parser.add_argument(
        "--name-pattern",
        type=str,
        default=None,
        help="Pattern to extract chat name from filename, with %%s as placeholder "
        "(e.g., 'WhatsApp-chatt med %%s')",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    try:
        process_input(input_path, output_path, args.your_name, args.name_pattern)
    except ValueError as e:
        print(f"Error: {e}")
        return 1

    return None


if __name__ == "__main__":
    main()

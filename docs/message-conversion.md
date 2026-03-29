# Message Conversion

Emoji Counter supports multiple chat export formats. This guide explains how to prepare your chat exports.

## Signal Messages

### Using sigtop

[sigtop](https://github.com/tbvdm/sigtop/) is a tool to extract messages from Signal Desktop. Follow these steps:

1. Install sigtop following their [installation instructions](https://github.com/tbvdm/sigtop/)
2. Run sigtop to export your Signal messages
3. This will create a directory with `.txt` files, one per conversation

### File Structure

Signal exports via sigtop have this structure:

```
messages/
├── FirstName1 LastName1 (phone number or unique ID).txt
├── FirstName2 LastName2 (phone number or unique ID).txt
├── Group Chat (unique ID).txt
└── ...
```

### Message Format

Each file contains messages in this format:

```
Conversation: FirstName1 LastName1 (unique ID)

From: FirstName1 LastName1 (unique ID)
Type: incoming
Sent: Tue, 13 Aug 2024 09:30:41 +0200
Received: Tue, 13 Aug 2024 14:45:13 +0200

Lorem ipsum... 😄

From: You
Type: outgoing
Sent: Fri, 4 Oct 2024 17:53:47 +0200

consectetur adipiscing elit... 🤔
```

## WhatsApp Messages

WhatsApp chat exports need to be converted to the supported format using `message-convert`.

### Exporting from WhatsApp

1. Open WhatsApp on your phone
2. Open the chat you want to export
3. Tap the menu (three dots) → More → Export chat
4. Choose "Without Media"
5. Save the `.txt` file

WhatsApp exports have this format:

```
2025-06-05 19:42 - Alice: Hello there!
2025-06-05 20:12 - Bob: Hi Alice 🙏
2025-06-05 20:13 - Alice: How are you?
```

### Converting WhatsApp Exports

Use the `message-convert` command to convert WhatsApp exports:

#### Single File

```bash
message-convert \
  -i "WhatsApp-chatt med John Doe.txt" \
  -o converted/john.txt \
  --your-name "Your Name" \
  --name-pattern "WhatsApp-chatt med %s"
```

#### Multiple Files

```bash
message-convert \
  -i whatsapp_exports/ \
  -o converted/ \
  --your-name "Your Name" \
  --name-pattern "WhatsApp-chatt med %s"
```

When converting a directory, output files are renamed to `{chat_name} (Whatsapp).txt`.

### Command Options

| Option | Required | Description |
|--------|----------|-------------|
| `-i, --input` | Yes | Input file or directory containing WhatsApp exports |
| `-o, --output` | Yes | Output file or directory for converted files |
| `--your-name` | No | Your display name in WhatsApp (messages from you become "You") |
| `--name-pattern` | No | Pattern to extract chat name from filename |

### Name Patterns

The `--name-pattern` option uses `%s` as a placeholder for the chat name:

| Pattern | Matches | Extracts |
|---------|---------|----------|
| `"WhatsApp-chatt med %s"` | `WhatsApp-chatt med John Doe.txt` | `John Doe` |
| `"WhatsApp Chat with %s"` | `WhatsApp Chat with Jane Smith.txt` | `Jane Smith` |
| `"Chat_%s_export"` | `Chat_Alice_export.txt` | `Alice` |
| `"%s"` (or omit option) | `John Doe.txt` | `John Doe` |

### Error: Pattern Does Not Match

If you see an error like:

```
Error: Filename 'chat.txt' does not match pattern 'WhatsApp-chatt med %s'
```

Either:
1. Update the pattern to match your filename format
2. Omit `--name-pattern` to use the full filename stem as the chat name

## Other Formats

The converter can be extended to support other chat formats. The key requirements are:

- Extract sender name
- Extract timestamp
- Extract message content
- Group messages by conversation

If you need support for another format, please [open an issue](https://github.com/simonthor/emoji-counter/issues) on GitHub.

# Emoji Extraction

Once your chat exports are in the correct format, use `emoji-extract` to extract emojis and save them to a SQLite database.

## Basic Usage

### Single File

Extract emojis from a single chat file:

```bash
emoji-extract -i messages/chat.txt -o data/emojis.sql
```

### Directory

Extract emojis from all files in a directory:

```bash
emoji-extract -i messages/ -o data/emojis.sql
```

The tool will process all `.txt` files in the directory.

## Command Options

| Option | Default | Description |
|--------|---------|-------------|
| `-i, --input` | (required) | Input file or directory containing message files |
| `-o, --output` | `./emojis.sql` | Output SQLite database file |

## What Gets Extracted

The extractor processes each message and:

1. **Identifies emojis** using the `emoji` Python library
2. **Extracts metadata**:
   - The emoji character itself
   - Message timestamp (from `Sent:` field)
   - Username (from `From:` field)
   - Chat name (from filename, excluding text in parentheses)
3. **Stores in SQLite** for efficient querying

### Chat Name Extraction

The chat name is derived from the filename:

| Filename | Extracted Chat Name |
|----------|---------------------|
| `John Doe (abc-123).txt` | `John Doe` |
| `Group Chat (xyz-789).txt` | `Group Chat` |
| `Alice (Whatsapp).txt` | `Alice` |

Text in parentheses is automatically removed.

## Output

The command outputs:

```
Processing: messages/chat1.txt
Found 42 emoji instances
Processing: messages/chat2.txt
Found 18 emoji instances
Exporting to: data/emojis.sql
Done!
```

The resulting SQLite database contains an `emojis` table with all extracted data. See [Database Schema](database-schema.md) for details.

## Examples

### Organize Data by Source

Keep different sources separate:

```bash
# Signal messages
emoji-extract -i signal_messages/ -o data/signal.sql

# WhatsApp messages
emoji-extract -i converted_whatsapp/ -o data/whatsapp.sql
```

Later, you can explore them together:

```bash
emoji-explore data/signal.sql data/whatsapp.sql
```

### Quick Test

Test with a single file first:

```bash
emoji-extract -i messages/test.txt -o /tmp/test.sql
emoji-explore /tmp/test.sql
```

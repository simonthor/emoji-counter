# Database Schema

The SQLite database contains a single table that stores all extracted emoji data.

## Table: `emojis`

| Column | Type | Description |
|--------|------|-------------|
| `emoji` | TEXT | The emoji character (e.g., 😄, 👍, ❤️) |
| `timestamp` | TEXT | ISO 8601 timestamp when the message was sent |
| `username` | TEXT | Name of the user who sent the emoji |
| `chat_name` | TEXT | Name of the chat/conversation |

### Indexes

No indexes are created by default. For large datasets (>1 million rows), consider adding indexes:

```sql
CREATE INDEX idx_timestamp ON emojis(timestamp);
CREATE INDEX idx_username ON emojis(username);
CREATE INDEX idx_chat_name ON emojis(chat_name);
CREATE INDEX idx_emoji ON emojis(emoji);
```

## Data Types

### emoji (TEXT)

Stores the actual emoji character as UTF-8 text.

Examples:
- `😄`
- `👍`
- `❤️`
- `🎉`

### timestamp (TEXT)

ISO 8601 format with timezone offset.

Format: `YYYY-MM-DDTHH:MM:SS+ZZ:ZZ`

Examples:
- `2024-08-13T09:30:41+02:00`
- `2025-06-05T19:42:00+02:00`

### username (TEXT)

The sender's display name as it appears in the message file.

Examples:
- `John Doe`
- `Alice Smith`
- `You` (for outgoing messages)

**Note:** When converting WhatsApp messages with `--your-name`, that name is replaced with "You".

### chat_name (TEXT)

The conversation name derived from the filename.

Examples:
- `John Doe` (from `John Doe (abc-123).txt`)
- `Family Group` (from `Family Group (xyz-789).txt`)
- `Alice` (from `Alice (Whatsapp).txt`)

Text in parentheses is automatically removed during extraction.

## Example Queries

### Count Total Emojis

```sql
SELECT COUNT(*) as total_emojis FROM emojis;
```

### Most Popular Emojis

```sql
SELECT emoji, COUNT(*) as count
FROM emojis
GROUP BY emoji
ORDER BY count DESC
LIMIT 10;
```

### Emojis by User

```sql
SELECT username, emoji, COUNT(*) as count
FROM emojis
GROUP BY username, emoji
ORDER BY username, count DESC;
```

### Emojis Over Time

```sql
SELECT DATE(timestamp) as date, COUNT(*) as count
FROM emojis
GROUP BY date
ORDER BY date;
```

### User Activity in Specific Chat

```sql
SELECT username, COUNT(*) as emoji_count
FROM emojis
WHERE chat_name = 'John Doe'
GROUP BY username
ORDER BY emoji_count DESC;
```

## Storage

The database uses SQLite's default page size (4096 bytes). 

Typical storage:
- **~100 bytes** per row (varies with text length)
- **~10 MB** per 100,000 emoji instances

## Database File

The SQLite database is a single `.sql` file that can be:

- Copied and shared
- Backed up easily
- Queried with any SQLite client
- Combined with other databases using `ATTACH DATABASE`

## Combining Databases

The dashboard automatically combines multiple databases when provided:

```bash
emoji-explore data/signal.sql data/whatsapp.sql
```

This queries both databases separately and merges results in memory, suffixing chat names with the database name.

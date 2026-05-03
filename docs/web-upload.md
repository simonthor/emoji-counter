# Web-Based File Upload

The Emoji Counter dashboard includes a built-in file upload feature that lets you process chat exports directly from your browser without using command-line tools.

## Getting Started

### Launch the Dashboard

Start the dashboard without specifying any database files:

```bash
emoji-explore
```

Then open [http://127.0.0.1:8050](http://127.0.0.1:8050) in your browser.
This is the same interface as the one you would see on [the website](https://emoji-counter.onrender.com), but running locally on your machine.

You'll see an "Upload Chat Data" section at the top of the page.

### Upload Process

1. **Select Format**: Click the format dropdown and choose:
   - **Signal**: For Signal desktop message exports
   - **WhatsApp**: For WhatsApp chat exports
   - **Messenger**: For Facebook Messenger data

2. **Select File**: Click "Choose File" or drag and drop your `.zip` file

3. **Processing**: The system will:
   - Extract the .zip file
   - Automatically detect and handle nested directory structures
   - Convert the format (if needed)
   - Extract emojis from messages
   - Create a SQLite database
   - Load the data into the dashboard

4. **View Results**: Once complete, the chart will display your emoji frequency data and you can use filters to explore

## Preparing Your Files

### Signal

Use [sigtop](https://github.com/tbvdm/sigtop/) to export your Signal messages:

1. Install and run sigtop
2. It will create a `messages/` directory with `.txt` files
3. Zip the entire `messages/` directory:
   ```bash
   zip -r Signal.zip messages/
   ```
4. Upload the `Signal.zip` file

**What to expect:**
- Each `.txt` file contains messages from one conversation
- Format: Includes timestamps, sender names, and message content
- Extractable data: Emojis, timestamps, usernames, chat names

### WhatsApp

Export your WhatsApp chats following [WhatsApp's official instructions](https://faq.whatsapp.com/1180414079177245/):

1. In WhatsApp, select each chat you want to analyze
2. Tap "More" > "Export chat"
3. Choose "Without media" for faster processing
4. Save the exported `.txt` file
5. Repeat for each chat you want to include
6. Create a `.zip` file containing all exports:
   ```bash
   zip -r WhatsApp.zip "WhatsApp Chat with Alice.txt" "WhatsApp Chat with Bob.txt"
   ```
7. Upload the `.zip` file

**File naming:**
- WhatsApp exports typically follow pattern: `WhatsApp Chat with {name}.txt` (English) or `WhatsApp-chatt med {name}.txt` (Swedish)
- The system automatically detects your naming pattern

**What to expect:**
- Messages with timestamps and sender names
- Format: `[timestamp] - sender: message`
- Extractable data: Emojis, timestamps, usernames, chat names

### Messenger

Download your Messenger data from Facebook:

1. Go to [Facebook Download Your Information](https://www.facebook.com/download/your_information)
2. Click "Download Your Information"
3. Select:
   - **Date range**: All time
   - **Format**: JSON
   - **Information types**: Messages
4. Download the file (this creates a `.zip` file)
5. Upload the `.zip` file directly

**File structure:**
- Facebook creates folders for each conversation
- Each folder contains `message_1.json`, `message_2.json`, etc.
- Also includes `e2ee_cutover/` folder (end-to-end encrypted messages)

**What to expect:**
- JSON-formatted messages with detailed metadata
- System handles nested directory structures automatically
- Extractable data: Emojis, timestamps, usernames, chat names

## Upload Options

### Chat Format Selection

The format dropdown lets you specify which messaging platform the data is from:

| Format | Source | Use When |
|--------|--------|----------|
| **Signal** | Signal Desktop (via sigtop) | Exporting from Signal using sigtop tool |
| **WhatsApp** | WhatsApp Chat Exports | Exporting from WhatsApp app or web |
| **Messenger** | Facebook Messenger | Downloaded from Facebook Download Your Information |

### File Upload

- **Drag and Drop**: Drag your `.zip` file directly into the upload area
- **Click to Select**: Click the upload area to open a file chooser
- **File Requirements**: Must be a `.zip` file containing message exports

## What Happens During Upload

### Automatic Processing Pipeline

When you upload a file, the system:

1. **Extracts**: Unzips the uploaded file to a temporary location
2. **Detects Structure**: Identifies nested directory layouts
   - Signal/WhatsApp: Can extract from nested `Signal/` or `WhatsApp/` directories
   - Messenger: Looks for `your_facebook_activity/messages/` structure
3. **Converts** (for WhatsApp and Messenger):
   - Reads native format files
   - Converts to standard text format
   - Extracts chat and user information
4. **Extracts Emojis**: Parses messages and identifies emoji usage
5. **Creates Database**: Builds a SQLite database with extracted emoji data
6. **Persists**: Saves database to `data/uploads/` for future sessions
7. **Displays**: Loads data into dashboard and updates chart

### Error Handling

If processing fails, you'll see an error message in the dashboard explaining the issue. Common problems:

- **Invalid .zip format**: Ensure the file is a valid zip archive
- **Unsupported format**: Verify you selected the correct format
- **Missing files**: Check that your export contains message files
- **Nested structure**: Ensure zip contains expected directory structure

## Managing Uploaded Data

### Viewing Loaded Databases

After successful upload, you'll see a "Loaded Databases:" section showing:

- Database filename: `emojis_{unique_id}_{source_name}.sql`
- File path: `data/uploads/emojis_{unique_id}_{source_name}.sql`

### Persistent Storage

All uploaded data is saved to the `data/uploads/` directory:

```
data/uploads/
├── emojis_a1b2c3d4_Signal.sql
├── emojis_e5f6g7h8_Whatsapp original.sql
└── emojis_i9j0k1l2_Messenger_json_only.sql
```

These databases persist between dashboard sessions, so you can:
- Restart the dashboard and keep your data
- Continue analyzing the same data
- Access the databases from command-line tools if needed

### Starting Fresh

To start with a clean dashboard:

1. Delete the `data/uploads/` directory:
   ```bash
   rm -rf data/uploads/
   ```

2. Restart the dashboard:
   ```bash
   emoji-explore
   ```

## Tips and Tricks

### Multiple Platforms

Upload data from different platforms to compare emoji usage:

1. Upload a Signal file → see Signal data
2. Upload a WhatsApp file → chat names automatically get "(Whatsapp)" suffix
3. Upload a Messenger file → chat names get "(Messenger)" suffix
4. Charts automatically show combined data from all platforms

### Large Exports

If your export is very large:

- WhatsApp: Export chats without media (much smaller)
- Messenger: Select specific date ranges if available
- Split into multiple uploads if needed

### Troubleshooting Uploads

**Upload takes too long:**
- Larger exports (500+ conversations) may take 10+ seconds
- Watch the browser tab title - "Updating..." indicates processing

**No data appears:**
- Check browser console (press F12) for error messages
- Verify the correct format was selected
- Ensure the .zip file contains valid message exports

**Wrong data loaded:**
- Verify you selected the correct chat format
- Check file structure matches the platform's export format

## Command-Line Alternative

If you prefer the command-line workflow, you can still use the traditional tools:

1. Convert format manually: `message-convert`
2. Extract emojis: `emoji-extract`
3. Launch dashboard with specific databases: `emoji-explore data/emojis.sql`

See [Command-Line Tools Documentation](message-conversion.md) for details.

## Next Steps

Once you've uploaded your data:

- Explore the [Dashboard Features](dashboard.md) to learn about charts and filters
- Compare data from multiple platforms
- Analyze your emoji usage patterns
- Save chart views for presentations

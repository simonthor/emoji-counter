# Dashboard Usage

The interactive dashboard lets you explore emoji usage patterns through visualizations and filters.

## Uploading Chat Data

### Quick Upload

The dashboard includes a built-in upload feature that lets you process chat exports without command-line tools:

1. **Select Format**: Choose the format of your chat data:
   - **Signal**: Exports from Signal desktop via sigtop
   - **WhatsApp**: Exported chats from WhatsApp
   - **Messenger**: Downloaded data from Facebook Messenger

2. **Upload File**: Drag and drop or click to select your `.zip` file

3. **Processing**: The system will automatically:
   - Extract the .zip file
   - Handle nested directory structures
   - Convert the format (if needed)
   - Extract emojis
   - Create a database in `data/uploads/`
   - Display the data in the chart

4. **View Results**: Once processing is complete, the chart will automatically update with your emoji frequency data

### Supported File Formats

- **Signal**: `.zip` file containing `.txt` message exports from sigtop
- **WhatsApp**: `.zip` file containing WhatsApp chat export(s)
- **Messenger**: `.zip` file downloaded from Facebook containing JSON message exports

### Tips for File Preparation

#### Signal: 
- Use [sigtop](https://github.com/tbvdm/sigtop/) to export your Signal messages, then zip the entire messages directory.

#### WhatsApp: 
- Export each chat individually following [WhatsApp's instructions](https://faq.whatsapp.com/1180414079177245/)
- Zip all your chat exports into a single `.zip` file
- Recommend exporting without media for faster processing

#### Messenger:
- Download your data from [Facebook's Download Your Information page](https://www.facebook.com/download/your_information)
- Select JSON format and "Messages" data type
- Remove the `photos/` folders, as these take up a lot os space and aren't needed for emoji analysis (optional but highly recommended)
Upload the downloaded `.zip` file directly

## Launching the Dashboard

### No Database (Upload Mode)

Start the dashboard without any databases to use the file upload feature:

```bash
emoji-explore
```

This allows you to upload chat exports directly through the web interface. Uploaded data will be saved to `data/uploads/` and automatically loaded into the dashboard.

Note that some charts and features might not show up immediately while it is processing the uploaded file. During this time, it will be written "Updating..." on the tab.

!!! warning "Warning" 
      Once processing is complete, the plots might still not show up and it might say "No data available". If this happens, click around a bit by e.g. selecting "Pie chart" or changing the filters for the User or Chat. This will trigger the dashboard to check for new data and update the charts.

### Single Database

View data from one source:

```bash
emoji-explore data/emojis.sql
```

### Multiple Databases

Combine and compare data from multiple sources:

```bash
emoji-explore data/signal.sql data/whatsapp.sql
```

When multiple databases are provided, chat names are automatically suffixed with the database filename to distinguish sources:

- `John Doe (signal)`
- `Alice (whatsapp)`

### Options

| Option | Default | Description |
|--------|---------|-------------|
| `db_paths` | (required) | One or more paths to SQLite databases |
| `--port` | `8050` | Port to run the server on |
| `--debug` | (disabled) | Enable debug mode and auto-reload |

### Accessing the Dashboard

After launching, open your browser to:

```
http://127.0.0.1:8050
```

Or use the custom port:

```bash
emoji-explore data/emojis.sql --port 3000
# Open http://127.0.0.1:3000
```

## Chart Types

### Bar Chart

Shows the total count for each emoji.

- Each bar represents one emoji
- Height indicates frequency
- Colors distinguish different emojis
- Hover to see exact counts

**Best for:** Comparing popularity of different emojis

### Pie Chart

Shows the proportional distribution of emoji usage.

- Each slice represents one emoji
- Size shows relative frequency
- Labels show emoji, count, and percentage
- Hover for detailed information

**Best for:** Understanding emoji distribution and proportions

### Time Series

Shows cumulative emoji usage over time.

- X-axis: Time (message timestamps)
- Y-axis: Cumulative count
- One line per emoji
- Bold black line shows total across all emojis
- Legend sorted by final cumulative count

**Best for:** Tracking emoji usage growth and trends

## Filters

### User Filter

Select a specific user or view everyone's emojis.

- Default: "Everyone"
- Updates chart to show only that user's emojis
- When changed, chat filter updates to show only chats where that user has messages

**Tip:** If "You" is in the list, it appears at the top for quick access.

### Chat Filter

Select a specific chat or view all chats.

- Default: "All Chats"
- Updates chart to show only emojis from that chat
- When changed, user filter updates to show only users in that chat

### Dynamic Filtering

Filters update dynamically based on each other:

1. Select a user → Chat dropdown shows only chats where that user participated
2. Select a chat → User dropdown shows only users in that chat
3. Select "Everyone" or "All Chats" to reset

This makes it easy to drill down into specific conversations or users.

## Interactive Controls

### Show All / Hide All Buttons

Toggle visibility of all emojis at once:

- **Show All**: Make all emoji traces visible
- **Hide All**: Hide all emoji traces (legendonly mode)

Available on bar charts and time series. 

**Note:** Due to a Plotly limitation, these buttons don't work correctly for pie charts.

### Legend Interactions

Click on legend entries to:

- **Single click**: Toggle that emoji's visibility
- Works on all chart types
- Hidden emojis are grayed out in the legend

### Hover Information

Hover over any data point to see:

- **Bar/Pie**: Emoji, count, and percentage
- **Time series**: Date, emoji, and cumulative count

## Tips and Tricks

### Comparing Platforms

Use multiple databases to compare Signal vs WhatsApp usage:

```bash
emoji-explore data/signal.sql data/whatsapp.sql
```

Chat names will be suffixed (e.g., "Alice (signal)", "Alice (whatsapp)") to distinguish between platforms.

### Finding Active Periods

Use the time series chart to identify:

- Periods of high emoji usage
- When specific emojis became popular
- Overall message activity trends

### User Analysis

1. Select "Time Series" chart type
2. Choose a specific user from the user filter
3. See that user's emoji usage evolution

### Chat Comparison

1. Select "Bar Chart" or "Pie Chart"
2. Choose "Everyone" for users
3. Switch between different chats to compare emoji preferences

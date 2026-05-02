# Dashboard Usage

The interactive dashboard lets you explore emoji usage patterns through visualizations and filters.

## Launching the Dashboard

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

# %%
import pandas as pd
import plotly.express as px
import sqlite3

# %%

conn = sqlite3.connect("data/emojis.sql")
df = pd.read_sql_query("SELECT * FROM emojis", conn)

df

# %%
df["username"].value_counts()

# %%
df["emoji"].value_counts()

# %%
# Plot the accumulated count of each emoji over time
df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
df_sorted = df.sort_values("timestamp")
df_sorted["emoji_count"] = df_sorted.groupby("emoji").cumcount() + 1

fig = px.line(
    df_sorted,
    x="timestamp",
    y="emoji_count",
    color="emoji",
    title="Accumulated Count of Each Emoji Over Time",
)
fig.show()
# %%

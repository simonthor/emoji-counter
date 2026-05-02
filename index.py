from emoji_counter.explore import EmojiExplorer
import dash
import os

app = dash.Dash(__name__)
server = app.server
explorer = EmojiExplorer(app)
host = os.getenv("HOST", "0.0.0.0")
port = int(os.getenv("PORT", 10000))
explorer.run(host=host, port=port)

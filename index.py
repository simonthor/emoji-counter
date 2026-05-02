from emoji_counter.explore import EmojiExplorer
import dash

app = dash.Dash(__name__)
server = app.server
explorer = EmojiExplorer(app)
explorer.run(port=8000)

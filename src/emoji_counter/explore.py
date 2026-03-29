#!/usr/bin/env python3
"""
Interactive Dash app for exploring emoji data from SQLite database.
"""

import argparse
import sqlite3
from pathlib import Path

import dash
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html
from dash.dependencies import Input, Output


class EmojiExplorer:
    """Interactive Dash dashboard for exploring emoji usage data from SQLite.

    Provides multiple visualization types (bar, pie, time series) with interactive
    controls. Uses :mod:`dash` for the web interface and :mod:`pandas` for data
    manipulation. All queries execute directly against SQLite to minimize memory usage.

    Must call :meth:`run` to start the web server after initialization.
    """

    def __init__(self, db_path: Path):
        """Initialize the explorer and configure the Dash application.

        Sets up the application layout and registers all interactive callbacks.
        Does not start the web server; call :meth:`run` separately.

        :param db_path: Path to SQLite database file containing ``emojis`` table.
        """
        self.db_path = db_path
        self.app = dash.Dash(__name__)
        self.setup_layout()
        self.setup_callbacks()

    def get_usernames(self):
        """Query database for all unique usernames.

        Returns a list of all distinct usernames that appear in the database,
        sorted alphabetically.

        :returns: List of username strings.
        """
        query = """
            SELECT DISTINCT username
            FROM emojis
            ORDER BY username
        """
        
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql(query, conn)
        conn.close()
        
        return df['username'].tolist()

    def get_chat_names(self):
        """Query database for all unique chat names.

        Returns a list of all distinct chat names that appear in the database,
        sorted alphabetically.

        :returns: List of chat name strings.
        """
        query = """
            SELECT DISTINCT chat_name
            FROM emojis
            ORDER BY chat_name
        """
        
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql(query, conn)
        conn.close()
        
        return df['chat_name'].tolist()

    def get_emoji_counts(self, username=None, chat_name=None):
        """Query database for total occurrence count of each emoji.

        Aggregates all emoji occurrences across all messages and dates, returning
        emojis sorted by frequency (most common first). Optionally filters by username
        and/or chat name.

        :param username: Optional username to filter by. If None, includes all users.
        :param chat_name: Optional chat name to filter by. If None, includes all chats.
        :returns: DataFrame with columns ``emoji`` and ``count``.
        """
        # Build WHERE clause based on filters
        where_clauses = []
        params = []
        
        if username:
            where_clauses.append("username = ?")
            params.append(username)
        if chat_name:
            where_clauses.append("chat_name = ?")
            params.append(chat_name)
        
        where_clause = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        query = f"""
            SELECT emoji, COUNT(*) as count
            FROM emojis
            {where_clause}
            GROUP BY emoji
            ORDER BY count DESC
        """
        
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql(query, conn, params=params if params else None)
        conn.close()
        
        return df

    def get_emoji_time_series(self, username=None, chat_name=None):
        """Query database for individual emoji occurrences with timestamps.

        Returns raw emoji data without aggregation. Each row represents one
        emoji occurrence with its full timestamp. Optionally filters by username
        and/or chat name.

        :param username: Optional username to filter by. If None, includes all users.
        :param chat_name: Optional chat name to filter by. If None, includes all chats.
        :returns: DataFrame with columns ``timestamp`` and ``emoji``.
        """
        # Build WHERE clause based on filters
        where_clauses = []
        params = []
        
        if username:
            where_clauses.append("username = ?")
            params.append(username)
        if chat_name:
            where_clauses.append("chat_name = ?")
            params.append(chat_name)
        
        where_clause = " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
        
        query = f"""
            SELECT 
                timestamp,
                emoji
            FROM emojis
            {where_clause}
            ORDER BY timestamp
        """
        
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql(query, conn, params=params if params else None)
        conn.close()
        
        return df

    def add_toggle_buttons(self, fig):
        """Add Show All / Hide All toggle buttons to a Plotly figure.

        Adds an updatemenus configuration with two buttons that control the
        visibility of all traces in the figure.

        :param fig: Plotly figure to add buttons to.
        :returns: The same figure with toggle buttons added.
        """
        fig.update_layout(
            updatemenus=[
                dict(
                    type="buttons",
                    direction="left",
                    buttons=[
                        dict(
                            args=[{"visible": True}],
                            label="Show All",
                            method="restyle"
                        ),
                        dict(
                            args=[{"visible": "legendonly"}],
                            label="Hide All",
                            method="restyle"
                        ),
                    ],
                    showactive=False,
                    x=0,
                    xanchor="left",
                    y=1.15,
                    yanchor="top"
                ),
            ]
        )
        return fig

    def setup_layout(self):
        """Configure the Dash application layout with controls and plot area.

        Creates dropdowns for chart type, user, and chat selection, and a graph
        container for plots. The layout is assigned to :attr:`self.app.layout`.
        """
        # Get list of usernames for dropdown
        usernames = self.get_usernames()
        # If "You" is in the list, move it to the top
        if "You" in usernames:
            usernames.remove("You")
            usernames.insert(0, "You")
        
        user_options = [{"label": "Everyone", "value": "everyone"}] + [
            {"label": username, "value": username} for username in usernames
        ]
        
        # Get list of chat names for dropdown
        chat_names = self.get_chat_names()
        chat_options = [{"label": "All Chats", "value": "all"}] + [
            {"label": chat_name, "value": chat_name} for chat_name in chat_names
        ]
        
        self.app.layout = html.Div(
            [
                html.H1("🎭 Emoji Explorer 📊", style={"textAlign": "center"}),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Label("Chart Type:"),
                                dcc.Dropdown(
                                    id="chart-type",
                                    options=[
                                        {"label": "Bar Chart", "value": "bar"},
                                        {"label": "Pie Chart", "value": "pie"},
                                        {"label": "Time Series", "value": "timeseries"},
                                    ],
                                    value="bar",
                                    clearable=False,
                                    style={"width": "200px"},
                                ),
                            ],
                            style={"display": "inline-block", "marginRight": "20px"},
                        ),
                        html.Div(
                            [
                                html.Label("User:"),
                                dcc.Dropdown(
                                    id="user-filter",
                                    options=user_options,
                                    value="everyone",
                                    clearable=False,
                                    style={"width": "200px"},
                                ),
                            ],
                            style={"display": "inline-block", "marginRight": "20px"},
                        ),
                        html.Div(
                            [
                                html.Label("Chat:"),
                                dcc.Dropdown(
                                    id="chat-filter",
                                    options=chat_options,
                                    value="all",
                                    clearable=False,
                                    style={"width": "200px"},
                                ),
                            ],
                            style={"display": "inline-block"},
                        ),
                    ],
                    style={"padding": "20px", "textAlign": "center"},
                ),
                html.Div(
                    [dcc.Graph(id="emoji-frequency-plot")], style={"padding": "20px"}
                ),
            ]
        )

    def setup_callbacks(self):
        """Register interactive callback for chart updates.

        Creates a callback to regenerate the plot when chart type, user, or chat filter changes.
        The callback is registered with the :attr:`self.app` instance.
        """

        @self.app.callback(
            Output("emoji-frequency-plot", "figure"),
            Input("chart-type", "value"),
            Input("user-filter", "value"),
            Input("chat-filter", "value")
        )
        def update_plot(chart_type, selected_user, selected_chat):
            """Generate a Plotly figure based on selected chart type and filters.

            Queries the database via :meth:`get_emoji_counts` or
            :meth:`get_emoji_time_series` depending on chart type, filtering by
            user and/or chat if specified. For time series, always shows cumulative counts.
            Returns a figure with appropriate traces, labels, and hover templates.

            :param chart_type: Chart type (``"bar"``, ``"pie"``, or ``"timeseries"``).
            :param selected_user: Username to filter by, or ``"everyone"`` for all users.
            :param selected_chat: Chat name to filter by, or ``"all"`` for all chats.
            :returns: Plotly :class:`go.Figure` ready for rendering.
            """
            # Convert dropdown values to None for query methods
            username = None if selected_user == "everyone" else selected_user
            chat_name = None if selected_chat == "all" else selected_chat
            
            if chart_type == "timeseries":
                # Get time series data from SQL
                df = self.get_emoji_time_series(username, chat_name)

                if df.empty:
                    return go.Figure().update_layout(
                        title="No data available",
                        xaxis={"visible": False},
                        yaxis={"visible": False},
                    )

                # Add cumulative count column
                df['count'] = 1
                df = df.sort_values('timestamp')
                df['cumcount'] = df.groupby('emoji')['count'].cumsum()

                # Get emoji order by final cumsum value (descending)
                emoji_order = df.groupby('emoji')['cumcount'].last().sort_values(ascending=False).index.tolist()

                # Create figure using plotly express with category order
                fig = px.line(
                    df,
                    x='timestamp',
                    y='cumcount',
                    color='emoji',
                    title='Emoji Usage Over Time',
                    category_orders={'emoji': emoji_order}
                )
                
                # Calculate and add total line
                df_total = df.copy()
                df_total['total'] = df_total['count'].cumsum()
                
                fig.add_trace(
                    go.Scatter(
                        x=df_total['timestamp'],
                        y=df_total['total'],
                        mode="lines",
                        name="Total",
                        line=dict(color="black"),
                        hovertemplate="<b>Total</b><br>Date: %{x}<br>Count: %{y}<extra></extra>",
                    )
                )
                
                # Move Total trace to the top of the legend
                fig.data = (fig.data[-1],) + fig.data[:-1]

                fig.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Count",
                    legend=dict(
                        orientation="v",
                        yanchor="top",
                        y=1,
                        xanchor="left",
                        x=1.02,
                    ),
                )

                return self.add_toggle_buttons(fig)

            # Get data from SQL for bar/pie charts
            df = self.get_emoji_counts(username, chat_name)

            if df.empty:
                # Return empty figure if no data
                return go.Figure().update_layout(
                    title="No data available",
                    xaxis={"visible": False},
                    yaxis={"visible": False},
                )

            if chart_type == "bar":
                fig = px.bar(
                    df,
                    x="emoji",
                    y="count",
                    color="emoji",
                    text="count",
                    title="Emoji Frequency (Bar Chart)",
                )
                fig.update_layout(
                    xaxis_title="Emoji",
                    yaxis_title="Count",
                    xaxis={"type": "category"},
                    hovermode="x",
                )
                fig.update_traces(textposition="auto")

            elif chart_type == "pie":
                fig = px.pie(
                    df,
                    names="emoji",
                    values="count",
                    title="Emoji Frequency (Pie Chart)",
                )
                fig.update_layout(
                    legend_title="emoji",
                )
                fig.update_traces(
                    textposition='inside',
                    textinfo='label+percent+value',
                    hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>",
                )

            return self.add_toggle_buttons(fig)

    def run(self, debug=True, port=8050):
        """Start the Dash web server and block until interrupted.

        Prints the database path and server URL to stdout, then starts the
        Flask development server. Blocks indefinitely until interrupted (Ctrl+C).

        :param debug: Enable debug mode with auto-reload and detailed errors.
        :param port: TCP port to bind the server to.
        """
        print(f"Loading data from: {self.db_path}")
        print(f"Starting Dash app on http://127.0.0.1:{port}")
        self.app.run(debug=debug, port=port)


def main():
    """Parse arguments, validate database path, and launch the dashboard.

    Parses command-line arguments for database path and server options. Validates
    that the database file exists before initializing :class:`EmojiExplorer`.
    Returns exit code ``1`` if the database is not found, otherwise blocks until
    the server is interrupted.

    :returns: Exit code ``1`` on error, or does not return if server starts successfully.
    """
    parser = argparse.ArgumentParser(
        description="Interactive dashboard for exploring emoji data"
    )
    parser.add_argument("db_path", type=str, help="Path to the SQLite database file")
    parser.add_argument(
        "--port",
        type=int,
        default=8050,
        help="Port to run the Dash app on (default: 8050)",
    )
    parser.add_argument("--no-debug", action="store_true", help="Disable debug mode")

    args = parser.parse_args()

    db_path = Path(args.db_path)

    if not db_path.exists():
        print(f"Error: Database file not found: {db_path}")
        return 1

    explorer = EmojiExplorer(db_path)
    explorer.run(debug=not args.no_debug, port=args.port)


if __name__ == "__main__":
    main()

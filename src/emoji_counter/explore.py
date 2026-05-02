#!/usr/bin/env python3
"""
Interactive Dash app for exploring emoji data from SQLite database(s).

Supports both command-line database paths and web-based file uploads
in various formats (Signal, WhatsApp, Messenger).

Security: Implements per-session database isolation to prevent cross-user
data access in multi-user deployments.
"""

import argparse
import base64
import shutil
import sqlite3
import tempfile
import time
import uuid
from pathlib import Path

import dash
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html
from dash.dependencies import Input, Output, State

from emoji_counter.upload_processor import process_uploaded_file

# Session database directory
SESSION_UPLOAD_ROOT = Path("data") / "uploads"


class EmojiExplorer:
    """
    Interactive Dash dashboard for exploring emoji usage data from SQLite.

    Provides multiple visualization types (bar, pie, time series) with interactive
    controls. Uses Dash for the web interface and pandas for data manipulation. All
    queries execute directly against SQLite to minimize memory usage.

    Supports multiple database files. When multiple files are provided, chat names
    are suffixed with the database file stem in parentheses to distinguish sources.

    Can be initialized with database paths or without. If initialized without paths,
    users can upload .zip files via the web interface to load and analyze data.

    SECURITY: Implements per-session isolation. Each user session has its own
    database storage directory, and database paths are stored in session-specific
    Dash Stores, not in global instance state.

    Attributes
    ----------
    app : dash.Dash
        The Dash application instance.
    initial_db_paths : list of Path
        Initial database paths provided at startup (shared, read-only).

    Notes
    -----
    Must call `run` to start the web server after initialization.
    Uploaded files are stored in: data/uploads/{session_id}/
    """

    def __init__(self, app: dash.Dash, db_paths: list[Path] | None = None) -> None:
        """
        Initialize the explorer and configure the Dash application.

        Sets up the application layout and registers all interactive callbacks.
        Does not start the web server; call `run` separately.

        Parameters
        ----------
        db_paths : list of Path, optional
            List of paths to SQLite database files containing emojis table.
            These are shared across all sessions (read-only).
            If None, users can upload files via the web interface.
        """
        self.initial_db_paths = db_paths if db_paths else []
        self.app = app
        self.setup_layout()
        self.setup_callbacks()

    def _query_all_databases(
        self, query: str, db_paths: list[Path] | None = None, params: list[str] | None = None
    ) -> pd.DataFrame:
        """
        Execute a query against specified databases and combine results.

        When multiple databases are used, adds a suffix to chat_name column
        based on the database file stem.

        Parameters
        ----------
        query : str
            SQL query to execute.
        db_paths : list of Path, optional
            List of database paths to query. If None, uses initial_db_paths.
            This should be session-specific paths from the caller.
        params : list of str, optional
            Query parameters for parameterized queries.

        Returns
        -------
        pd.DataFrame
            Combined DataFrame from all databases.
        """
        if db_paths is None:
            db_paths = self.initial_db_paths
        
        dfs: list[pd.DataFrame] = []
        use_suffix = len(db_paths) > 1

        for db_path in db_paths:
            db_path = Path(db_path)
            if not db_path.exists():
                continue
            conn = sqlite3.connect(db_path)
            df = pd.read_sql(query, conn, params=params if params else None)
            conn.close()

            if use_suffix and "chat_name" in df.columns:
                suffix = f" ({db_path.stem})"
                df["chat_name"] = df["chat_name"] + suffix

            dfs.append(df)

        if not dfs:
            return pd.DataFrame()

        return pd.concat(dfs, ignore_index=True)

    def get_usernames(self, db_paths: list[Path] | None = None, chat_name: str | None = None) -> list[str]:
        """
        Query database(s) for unique usernames, optionally filtered by chat.

        Returns a list of all distinct usernames that appear in the database(s),
        sorted alphabetically. If chat_name is provided, only returns users who
        have messages in that chat.

        Parameters
        ----------
        db_paths : list of Path, optional
            List of database paths to query. If None, uses initial_db_paths.
        chat_name : str, optional
            Chat name to filter by. If None, returns all usernames.

        Returns
        -------
        list of str
            List of username strings, sorted alphabetically.
        """
        if chat_name:
            usernames = self._get_usernames_for_chat(db_paths, chat_name)
        else:
            query = "SELECT DISTINCT username FROM emojis"
            df = self._query_all_databases(query, db_paths)
            if df.empty:
                return []
            usernames = df["username"].unique().tolist()

        return sorted(usernames)

    def _get_usernames_for_chat(self, db_paths: list[Path] | None = None, chat_name: str | None = None) -> list[str]:
        """
        Get usernames that have messages in a specific chat.

        Parameters
        ----------
        db_paths : list of Path, optional
            List of database paths to query.
        chat_name : str
            Chat name to filter by (may include database suffix).

        Returns
        -------
        list of str
            List of username strings.
        """
        if db_paths is None:
            db_paths = self.initial_db_paths
        
        if chat_name is None:
            return []
            
        use_suffix = len(db_paths) > 1
        usernames: set[str] = set()

        for db_path in db_paths:
            db_path = Path(db_path)
            if not db_path.exists():
                continue
                
            if use_suffix:
                suffix = f" ({db_path.stem})"
                if chat_name.endswith(suffix):
                    original_name = chat_name[: -len(suffix)]
                else:
                    continue
            else:
                original_name = chat_name

            query = "SELECT DISTINCT username FROM emojis WHERE chat_name = ?"
            conn = sqlite3.connect(db_path)
            df = pd.read_sql(query, conn, params=[original_name])
            conn.close()

            usernames.update(df["username"].tolist())

        return list(usernames)

    def get_chat_names(self, db_paths: list[Path] | None = None, username: str | None = None) -> list[str]:
        """
        Query database(s) for unique chat names, optionally filtered by user.

        Returns a list of all distinct chat names that appear in the database(s),
        sorted alphabetically. When multiple databases are used, chat names include
        a suffix indicating the source database. If username is provided, only
        returns chats where that user has messages.

        Parameters
        ----------
        db_paths : list of Path, optional
            List of database paths to query. If None, uses initial_db_paths.
        username : str, optional
            Username to filter by. If None, returns all chat names.

        Returns
        -------
        list of str
            List of chat name strings, sorted alphabetically.
        """
        if db_paths is None:
            db_paths = self.initial_db_paths
            
        use_suffix = len(db_paths) > 1
        chat_names: list[str] = []

        for db_path in db_paths:
            db_path = Path(db_path)
            if not db_path.exists():
                continue
                
            if username:
                query = "SELECT DISTINCT chat_name FROM emojis WHERE username = ?"
                params: list[str] | None = [username]
            else:
                query = "SELECT DISTINCT chat_name FROM emojis"
                params = None

            conn = sqlite3.connect(db_path)
            df = pd.read_sql(query, conn, params=params)
            conn.close()

            names = df["chat_name"].tolist()
            if use_suffix:
                suffix = f" ({db_path.stem})"
                names = [name + suffix for name in names]

            chat_names.extend(names)

        return sorted(set(chat_names))

    def get_emoji_counts(
        self, db_paths: list[Path] | None = None, username: str | None = None, chat_name: str | None = None
    ) -> pd.DataFrame:
        """
        Query database(s) for total occurrence count of each emoji.

        Aggregates all emoji occurrences across all messages and dates, returning
        emojis sorted by frequency (most common first). Optionally filters by username
        and/or chat name.

        Parameters
        ----------
        db_paths : list of Path, optional
            List of database paths to query. If None, uses initial_db_paths.
        username : str, optional
            Username to filter by. If None, includes all users.
        chat_name : str, optional
            Chat name to filter by. If None, includes all chats.

        Returns
        -------
        pd.DataFrame
            DataFrame with columns 'emoji' and 'count', sorted by count descending.
        """
        if db_paths is None:
            db_paths = self.initial_db_paths
            
        # For chat_name filter with multiple DBs, we need to handle the suffix
        use_suffix = len(db_paths) > 1

        dfs: list[pd.DataFrame] = []

        for db_path in db_paths:
            db_path = Path(db_path)
            if not db_path.exists():
                continue
                
            # Build WHERE clause based on filters
            where_clauses: list[str] = []
            params: list[str] = []

            if username:
                where_clauses.append("username = ?")
                params.append(username)

            if chat_name:
                if use_suffix:
                    # Check if this chat_name belongs to this database
                    suffix = f" ({db_path.stem})"
                    if chat_name.endswith(suffix):
                        # Strip suffix and filter by original name
                        original_name = chat_name[: -len(suffix)]
                        where_clauses.append("chat_name = ?")
                        params.append(original_name)
                    else:
                        # This chat_name doesn't belong to this database
                        continue
                else:
                    where_clauses.append("chat_name = ?")
                    params.append(chat_name)

            where_clause = (
                " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
            )

            query = f"""
                SELECT emoji, COUNT(*) as count
                FROM emojis
                {where_clause}
                GROUP BY emoji
            """

            conn = sqlite3.connect(db_path)
            df = pd.read_sql(query, conn, params=params if params else None)
            conn.close()

            dfs.append(df)

        if not dfs:
            return pd.DataFrame(columns=["emoji", "count"])

        # Combine and re-aggregate
        combined = pd.concat(dfs, ignore_index=True)
        if combined.empty:
            return pd.DataFrame(columns=["emoji", "count"])

        result = combined.groupby("emoji", as_index=False)["count"].sum()
        return result.sort_values("count", ascending=False)

    def get_emoji_time_series(
        self, db_paths: list[Path] | None = None, username: str | None = None, chat_name: str | None = None
    ) -> pd.DataFrame:
        """
        Query database(s) for individual emoji occurrences with timestamps.

        Returns raw emoji data without aggregation. Each row represents one
        emoji occurrence with its full timestamp. Optionally filters by username
        and/or chat name.

        Parameters
        ----------
        db_paths : list of Path, optional
            List of database paths to query. If None, uses initial_db_paths.
        username : str, optional
            Username to filter by. If None, includes all users.
        chat_name : str, optional
            Chat name to filter by. If None, includes all chats.

        Returns
        -------
        pd.DataFrame
            DataFrame with columns 'timestamp' and 'emoji', sorted by timestamp.
        """
        if db_paths is None:
            db_paths = self.initial_db_paths
            
        use_suffix = len(db_paths) > 1

        dfs: list[pd.DataFrame] = []

        for db_path in db_paths:
            db_path = Path(db_path)
            if not db_path.exists():
                continue
                
            # Build WHERE clause based on filters
            where_clauses: list[str] = []
            params: list[str] = []

            if username:
                where_clauses.append("username = ?")
                params.append(username)

            if chat_name:
                if use_suffix:
                    # Check if this chat_name belongs to this database
                    suffix = f" ({db_path.stem})"
                    if chat_name.endswith(suffix):
                        original_name = chat_name[: -len(suffix)]
                        where_clauses.append("chat_name = ?")
                        params.append(original_name)
                    else:
                        continue
                else:
                    where_clauses.append("chat_name = ?")
                    params.append(chat_name)

            where_clause = (
                " WHERE " + " AND ".join(where_clauses) if where_clauses else ""
            )

            query = f"""
                SELECT timestamp, emoji
                FROM emojis
                {where_clause}
            """

            conn = sqlite3.connect(db_path)
            df = pd.read_sql(query, conn, params=params if params else None)
            conn.close()

            dfs.append(df)

        if not dfs:
            return pd.DataFrame(columns=["timestamp", "emoji"])

        combined = pd.concat(dfs, ignore_index=True)
        return combined.sort_values("timestamp")

    def add_toggle_buttons(self, fig: go.Figure) -> go.Figure:
        """
        Add Show All / Hide All toggle buttons to a Plotly figure.

        Adds an updatemenus configuration with two buttons that control the
        visibility of all traces in the figure.

        Parameters
        ----------
        fig : go.Figure
            Plotly figure to add buttons to.

        Returns
        -------
        go.Figure
            The same figure with toggle buttons added.
        """
        fig.update_layout(
            updatemenus=[
                dict(
                    type="buttons",
                    direction="left",
                    buttons=[
                        dict(
                            args=[{"visible": True}], label="Show All", method="restyle"
                        ),
                        dict(
                            args=[{"visible": "legendonly"}],
                            label="Hide All",
                            method="restyle",
                        ),
                    ],
                    showactive=False,
                    x=0,
                    xanchor="left",
                    y=1.15,
                    yanchor="top",
                ),
            ]
        )
        return fig

    def setup_layout(self) -> None:
        """
        Configure the Dash application layout with controls, plot area, and file upload.

        Creates sections for file upload (when needed), database status, chart controls,
        and graph display. Uses per-session Store components to maintain state of 
        loaded databases, ensuring user isolation.
        Includes dropdowns for chart type, user, and chat selection.
        """
        # Generate session ID for this user
        session_id = str(uuid.uuid4())

        self.app.layout = html.Div(
            [
                # Session identifier - stored in browser session storage, not shared
                dcc.Store(id="session-id", data=session_id, storage_type="session"),
                # Per-session database paths - using session storage for isolation
                dcc.Store(id="db-paths-store", data=[str(p) for p in self.initial_db_paths], storage_type="session"),
                html.H1("🎭 Emoji Explorer 📊", style={"textAlign": "center"}),
                # Upload section
                html.Div(
                    id="upload-section",
                    children=[
                        html.Hr(),
                        html.Div(
                            [
                                html.H2(
                                    "Upload Chat Data", style={"textAlign": "center"}
                                ),
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.Label("Chat Format:"),
                                                dcc.Dropdown(
                                                    id="format-selector",
                                                    options=[
                                                        {
                                                            "label": "Signal",
                                                            "value": "Signal",
                                                        },
                                                        {
                                                            "label": "WhatsApp",
                                                            "value": "Whatsapp",
                                                        },
                                                        {
                                                            "label": "Messenger",
                                                            "value": "Messenger",
                                                        },
                                                    ],
                                                    value="Signal",
                                                    clearable=False,
                                                    style={"width": "150px"},
                                                ),
                                            ],
                                            style={
                                                "display": "inline-block",
                                                "marginRight": "20px",
                                            },
                                        ),
                                        html.Div(
                                            [
                                                dcc.Upload(
                                                    id="file-upload",
                                                    children=html.Div(
                                                        [
                                                            "Drag and drop or ",
                                                            html.A(
                                                                "select a .zip file"
                                                            ),
                                                        ]
                                                    ),
                                                    style={
                                                        "width": "100%",
                                                        "height": "60px",
                                                        "lineHeight": "60px",
                                                        "borderWidth": "1px",
                                                        "borderStyle": "dashed",
                                                        "borderRadius": "5px",
                                                        "textAlign": "center",
                                                        "margin": "10px",
                                                    },
                                                    multiple=False,
                                                )
                                            ],
                                            style={
                                                "display": "inline-block",
                                                "width": "300px",
                                            },
                                        ),
                                    ],
                                    style={"textAlign": "center", "padding": "20px"},
                                ),
                                html.Div(
                                    [
                                        "Not working? Check the ",
                                        html.A(
                                            "documentation",
                                            href="https://simonthor.github.io/emoji-counter/dashboard/",
                                            target="_blank",
                                        ),
                                        ". Found a bug? ",
                                        html.A(
                                            "Report it on Github.",
                                            href="https://github.com/simonthor/emoji-counter/issues",
                                            target="_blank",
                                        ),
                                    ],
                                    style={
                                        "textAlign": "center",
                                        "color": "#666",
                                        "fontSize": "0.9rem",
                                        "paddingBottom": "20px",
                                    },
                                ),
                                html.Div(id="upload-status", style={"padding": "10px"}),
                            ],
                            style={
                                "border": "1px solid #ddd",
                                "borderRadius": "5px",
                                "padding": "20px",
                                "margin": "20px",
                                "backgroundColor": "#f9f9f9",
                            },
                        ),
                    ],
                    style={"display": "block" if not self.initial_db_paths else "none"},
                ),
                # Main dashboard section
                html.Div(
                    id="dashboard-section",
                    children=[
                        html.Hr(),
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
                                                {
                                                    "label": "Time Series",
                                                    "value": "timeseries",
                                                },
                                            ],
                                            value="bar",
                                            clearable=False,
                                            style={"width": "200px"},
                                        ),
                                    ],
                                    style={
                                        "display": "inline-block",
                                        "marginRight": "20px",
                                    },
                                ),
                                html.Div(
                                    [
                                        html.Label("User:"),
                                        dcc.Dropdown(
                                            id="user-filter",
                                            value="everyone",
                                            clearable=False,
                                            style={"width": "200px"},
                                        ),
                                    ],
                                    style={
                                        "display": "inline-block",
                                        "marginRight": "20px",
                                    },
                                ),
                                html.Div(
                                    [
                                        html.Label("Chat:"),
                                        dcc.Dropdown(
                                            id="chat-filter",
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
                            [dcc.Graph(id="emoji-frequency-plot")],
                            style={"padding": "20px"},
                        ),
                        html.Div(
                            "Shortcut: Press Alt+S to save the current chart view.",
                            style={
                                "textAlign": "center",
                                "color": "#666",
                                "fontSize": "0.9rem",
                                "paddingBottom": "20px",
                            },
                        ),
                        html.Div(
                            [
                                "Not working? Check the ",
                                html.A(
                                    "documentation",
                                    href="https://simonthor.github.io/emoji-counter/dashboard/",
                                    target="_blank",
                                ),
                                ". Found a bug? ",
                                html.A(
                                    "Report it on Github.",
                                    href="https://github.com/simonthor/emoji-counter/issues",
                                    target="_blank",
                                ),
                            ],
                            style={
                                "textAlign": "center",
                                "color": "#666",
                                "fontSize": "0.9rem",
                                "paddingBottom": "20px",
                            },
                        ),
                    ],
                    style={"display": "block" if self.initial_db_paths else "none"},
                ),
            ]
        )

    def _build_user_options(self, db_paths: list[Path] | None = None, chat_name: str | None = None) -> list[dict[str, str]]:
        """
        Build user dropdown options, optionally filtered by chat.

        Parameters
        ----------
        db_paths : list of Path, optional
            List of database paths to query.
        chat_name : str, optional
            Chat name to filter users by.

        Returns
        -------
        list of dict
            List of dropdown option dicts with 'label' and 'value' keys.
        """
        usernames = self.get_usernames(db_paths, chat_name)
        # If "You" is in the list, move it to the top
        if "You" in usernames:
            usernames.remove("You")
            usernames.insert(0, "You")

        return [{"label": "Everyone", "value": "everyone"}] + [
            {"label": username, "value": username} for username in usernames
        ]

    def _build_chat_options(self, db_paths: list[Path] | None = None, username: str | None = None) -> list[dict[str, str]]:
        """
        Build chat dropdown options, optionally filtered by user.

        Parameters
        ----------
        db_paths : list of Path, optional
            List of database paths to query.
        username : str, optional
            Username to filter chats by.

        Returns
        -------
        list of dict
            List of dropdown option dicts with 'label' and 'value' keys.
        """
        chat_names = self.get_chat_names(db_paths, username)

        return [{"label": "All Chats", "value": "all"}] + [
            {"label": chat_name, "value": chat_name} for chat_name in chat_names
        ]

    def setup_callbacks(self) -> None:
        """
        Register interactive callbacks for chart and filter updates.

        Creates callbacks to:
        1. Handle file uploads and process chat data
        2. Update user dropdown options based on selected chat
        3. Update chat dropdown options based on selected user
        4. Regenerate the plot when any filter changes

        The callbacks are registered with the self.app instance.
        """

        @self.app.callback(
            Output("db-paths-store", "data"),
            Output("upload-status", "children"),
            Output("upload-section", "style"),
            Output("dashboard-section", "style"),
            Input("file-upload", "contents"),
            State("file-upload", "filename"),
            State("format-selector", "value"),
            State("db-paths-store", "data"),
            State("session-id", "data"),
            prevent_initial_call=True,
        )
        def handle_file_upload(
            contents: str | None,
            filename: str | None,
            chat_format: str,
            stored_db_paths: list[str],
            session_id: str,
        ) -> tuple[
            list[str],
            html.Div,
            dict[str, str],
            dict[str, str],
        ]:
            """
            Handle file upload, process data, and update dashboard state.

            SECURITY: Creates session-specific directories and stores paths in
            per-session storage to ensure user isolation in multi-user deployments.

            Processes the uploaded .zip file in the specified format,
            extracts emojis, and adds the resulting database to the list
            of loaded databases for THIS SESSION ONLY.

            Parameters
            ----------
            contents : str or None
                Base64-encoded file contents from the upload component.
            filename : str or None
                Original filename of the uploaded file.
            chat_format : str
                Selected chat format (Signal, Whatsapp, or Messenger).
            stored_db_paths : list of str
                Current list of loaded database paths for this session.
            session_id : str
                Unique session identifier for this user.

            Returns
            -------
            tuple
                Updated db paths, status message, and UI visibility styles.
            """
            if not contents or not filename:
                return (
                    stored_db_paths,
                    html.Div("No file selected", style={"color": "red"}),
                    {"display": "block"},
                    {"display": "none" if not stored_db_paths else "block"},
                )

            try:
                # Decode the uploaded file
                content_type, content_string = contents.split(",")
                zip_bytes = base64.b64decode(content_string)

                # Create session-specific directory for this user's uploads
                session_db_dir = SESSION_UPLOAD_ROOT / session_id
                session_db_dir.mkdir(parents=True, exist_ok=True)

                # Process the uploaded file in a temporary location
                with tempfile.TemporaryDirectory() as temp_dir:
                    output_db_path = Path(temp_dir) / "emojis.sql"

                    process_uploaded_file(
                        zip_bytes,
                        chat_format,
                        output_db_path,
                    )

                    # Copy the database to the session-specific directory
                    # This ensures different sessions have separate storage
                    persistent_db_path = (
                        session_db_dir
                        / f"emojis_{uuid.uuid4().hex[:8]}_{filename.replace('.zip', '.sql')}"
                    )
                    shutil.copy2(output_db_path, persistent_db_path)

                    # Update the stored paths (session-scoped only)
                    updated_paths = stored_db_paths + [str(persistent_db_path)]

                    # Create success message
                    status_msg = html.Div(
                        f"Successfully loaded data from {filename}",
                        style={"color": "green", "padding": "10px"},
                    )

                    return (
                        updated_paths,
                        status_msg,
                        {"display": "none"},  # Hide upload section
                        {"display": "block"},  # Show dashboard section
                    )

            except Exception as e:
                error_msg = html.Div(
                    f"Error processing file: {str(e)}",
                    style={"color": "red", "padding": "10px"},
                )
                return (
                    stored_db_paths,
                    error_msg,
                    {"display": "block"},  # Keep upload section visible
                    {
                        "display": "block" if stored_db_paths else "none"
                    },  # Keep dashboard if other DBs exist
                )

        @self.app.callback(
            Output("user-filter", "options"),
            Input("chat-filter", "value"),
            State("db-paths-store", "data"),
        )
        def update_user_options(selected_chat: str, stored_db_paths: list[str]) -> list[dict[str, str]]:
            """
            Update user dropdown options based on selected chat.

            Parameters
            ----------
            selected_chat : str
                Selected chat value from dropdown, or "all" for all chats.
            stored_db_paths : list of str
                Session-specific database paths.

            Returns
            -------
            list of dict
                User dropdown options filtered by chat.
            """
            db_paths = [Path(p) for p in stored_db_paths] if stored_db_paths else None
            chat_name = None if selected_chat == "all" else selected_chat
            return self._build_user_options(db_paths, chat_name)

        @self.app.callback(
            Output("chat-filter", "options"),
            Input("user-filter", "value"),
            State("db-paths-store", "data"),
        )
        def update_chat_options(selected_user: str, stored_db_paths: list[str]) -> list[dict[str, str]]:
            """
            Update chat dropdown options based on selected user.

            Parameters
            ----------
            selected_user : str
                Selected user value from dropdown, or "everyone" for all users.
            stored_db_paths : list of str
                Session-specific database paths.

            Returns
            -------
            list of dict
                Chat dropdown options filtered by user.
            """
            db_paths = [Path(p) for p in stored_db_paths] if stored_db_paths else None
            username = None if selected_user == "everyone" else selected_user
            return self._build_chat_options(db_paths, username)

        @self.app.callback(
            Output("emoji-frequency-plot", "figure"),
            Input("chart-type", "value"),
            Input("user-filter", "value"),
            Input("chat-filter", "value"),
            State("db-paths-store", "data"),
        )
        def update_plot(
            chart_type: str, selected_user: str, selected_chat: str, stored_db_paths: list[str]
        ) -> go.Figure:
            """
            Generate a Plotly figure based on selected chart type and filters.

            Queries the database via get_emoji_counts or get_emoji_time_series
            depending on chart type, filtering by user and/or chat if specified.
            For time series, always shows cumulative counts. Returns a figure
            with appropriate traces, labels, and hover templates.

            SECURITY: Uses session-specific database paths only.

            Parameters
            ----------
            chart_type : str
                Chart type: "bar", "pie", or "timeseries".
            selected_user : str
                Username to filter by, or "everyone" for all users.
            selected_chat : str
                Chat name to filter by, or "all" for all chats.
            stored_db_paths : list of str
                Session-specific database paths.

            Returns
            -------
            go.Figure
                Plotly figure ready for rendering.
            """
            db_paths = [Path(p) for p in stored_db_paths] if stored_db_paths else None
            
            # Convert dropdown values to None for query methods
            username = None if selected_user == "everyone" else selected_user
            chat_name = None if selected_chat == "all" else selected_chat

            if chart_type == "timeseries":
                # Get time series data from SQL
                df = self.get_emoji_time_series(db_paths, username, chat_name)

                if df.empty:
                    return go.Figure().update_layout(
                        title="No data available",
                        xaxis={"visible": False},
                        yaxis={"visible": False},
                    )

                # Add cumulative count column
                df["count"] = 1
                df = df.sort_values("timestamp")
                df["cumcount"] = df.groupby("emoji")["count"].cumsum()

                # Get emoji order by final cumsum value (descending)
                emoji_order = (
                    df.groupby("emoji")["cumcount"]
                    .last()
                    .sort_values(ascending=False)  # type: ignore
                    .index.tolist()
                )

                # Create figure using plotly express with category order
                fig = px.line(
                    df,
                    x="timestamp",
                    y="cumcount",
                    color="emoji",
                    title="Emoji Usage Over Time",
                    category_orders={"emoji": emoji_order},
                )

                # Calculate and add total line
                df_total = df.copy()
                df_total["total"] = df_total["count"].cumsum()

                fig.add_trace(
                    go.Scatter(
                        x=df_total["timestamp"],
                        y=df_total["total"],
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
            df = self.get_emoji_counts(db_paths, username, chat_name)

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
                    textposition="inside",
                    textinfo="label+percent+value",
                    hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>",
                )

            return self.add_toggle_buttons(fig)

    def run(
        self, debug: bool = False, host: str = "127.0.0.1", port: int = 8050, **kwargs
    ) -> None:
        """
        Start the Dash web server and block until interrupted.

        Prints the database path(s) and server URL to stdout, then starts the
        Flask development server. Blocks indefinitely until interrupted with Ctrl+C.

        Parameters
        ----------
        debug : bool, default=True
            Enable debug mode with auto-reload and detailed errors.
        port : int, default=8050
            TCP port to bind the server to.
        """
        for db_path in self.initial_db_paths:
            print(f"Loading data from: {db_path}")
        print(f"Starting Dash app on http://{host}:{port} ...")
        self.app.run(debug=debug, host=host, port=port, **kwargs)


def cleanup_old_uploads(max_age_hours: int = 2) -> None:
    """
    Remove old session upload directories to free disk space and reduce security risks.

    Session upload directories older than max_age_hours are deleted recursively.
    This prevents accumulation of stale data and reduces exposure window for
    uploaded files in ephemeral storage environments.

    Parameters
    ----------
    max_age_hours : int, default=2
        Maximum age of upload directories in hours. Directories older than this
        are deleted.
    """
    if not SESSION_UPLOAD_ROOT.exists():
        return

    max_age_seconds = max_age_hours * 3600
    current_time = time.time()

    for session_dir in SESSION_UPLOAD_ROOT.iterdir():
        if not session_dir.is_dir():
            continue

        dir_age_seconds = current_time - session_dir.stat().st_mtime
        if dir_age_seconds > max_age_seconds:
            try:
                shutil.rmtree(session_dir)
            except OSError as e:
                print(f"Warning: Failed to delete old upload directory {session_dir}: {e}")


def main() -> int | None:
    """
    Parse arguments, validate database paths, and launch the dashboard.

    Parses command-line arguments for database path(s) and server options. Validates
    that all database files exist before initializing EmojiExplorer. If no database
    paths are provided, starts the dashboard in upload mode where users can upload
    .zip files via the web interface.

    Returns
    -------
    int or None
        Exit code 1 on error, or does not return if server starts successfully.
    """
    parser = argparse.ArgumentParser(
        description="Interactive dashboard for exploring emoji data"
    )
    parser.add_argument(
        "db_paths",
        type=str,
        nargs="*",
        help="Path(s) to SQLite database file(s). If not provided, start in upload mode.",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8050,
        help="Port to run the Dash app on (default: 8050)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    cleanup_old_uploads()

    db_paths: list[Path] = []
    for path_str in args.db_paths:
        db_path = Path(path_str)
        if not db_path.exists():
            print(f"Error: Database file not found: {db_path}")
            return 1
        db_paths.append(db_path)

    app = dash.Dash(__name__)
    explorer = EmojiExplorer(app, db_paths if db_paths else None)
    explorer.run(debug=args.debug, port=args.port)
    return None


if __name__ == "__main__":
    main()

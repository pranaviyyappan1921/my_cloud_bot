"""
Future Connectable Integrations Catalog for Cloud AI Chatbot.

Defines rich connectable cards for:
- Gmail (Productivity)
- GitHub (Developer Tools)
- Google Drive (Productivity)
- Outlook (Productivity)
- Google Calendar (Productivity)
- Slack (Productivity)
- Dropbox (Cloud)
- Notion (Productivity)
- Databases (PostgreSQL / SQL Server / MySQL)

Each integration has structured permissions, schema specifications, and safe handlers.
Starts in DISCONNECTED state (is_connected=False) so users can discover, connect, and configure them.
"""

from typing import Dict, Any, Optional
from .base_plugin import BasePlugin, PluginPermission, PluginToolParameter, PluginToolSchema


class GmailPlugin(BasePlugin):
    def __init__(self):
        super().__init__(
            id="gmail",
            name="Gmail",
            description="Search your Gmail inbox, summarize email threads, and draft smart replies with AI assistance.",
            category="Productivity",
            icon="✉️",
            icon_bg="linear-gradient(135deg, #ea4335, #c5221f)",
            version="1.0.0",
            author="Google Workspace",
            tags=["Email", "Inbox", "Google", "Productivity"],
            requires_auth=True,
            is_connected=False,
            is_enabled=False,
        )

    def setup_permissions(self) -> None:
        self.add_permission(
            PluginPermission(
                id="gmail_read",
                name="Read Email Threads & Messages",
                description="Allows searching and summarizing emails in your inbox.",
                enabled=True,
                required=True,
            )
        )
        self.add_permission(
            PluginPermission(
                id="gmail_draft",
                name="Create Draft Emails",
                description="Allows preparing draft replies for your review.",
                enabled=True,
                required=False,
            )
        )

    def setup_tools(self) -> None:
        self.add_tool(
            PluginToolSchema(
                name="search_emails",
                description="Searches Gmail for messages matching keywords, senders, or labels.",
                parameters=[
                    PluginToolParameter(name="query", type="string", description="Search query string.", required=True),
                    PluginToolParameter(name="max_results", type="integer", description="Max messages to fetch (default 5).", required=False, default=5),
                ],
                required_permission="gmail_read",
            )
        )

    def execute(self, tool_name: str, params: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        valid, err = self.validate_tool_call(tool_name, params)
        if not valid:
            return {"success": False, "error": err, "summary": f"Failed: {err}"}
        query = params.get("query", "")
        return {
            "success": True,
            "summary": f"Gmail connected: Ready to search emails matching '{query}'.",
            "data": {"query": query, "status": "active_integration"},
        }


class GitHubPlugin(BasePlugin):
    def __init__(self):
        super().__init__(
            id="github",
            name="GitHub",
            description="Search repositories, review pull requests, inspect commits, and manage issues across your GitHub projects.",
            category="Developer Tools",
            icon="🐙",
            icon_bg="linear-gradient(135deg, #24292e, #181717)",
            version="1.0.0",
            author="GitHub / Microsoft",
            tags=["Git", "Code", "Repositories", "Issues", "Developer"],
            requires_auth=True,
            is_connected=False,
            is_enabled=False,
        )

    def setup_permissions(self) -> None:
        self.add_permission(
            PluginPermission(
                id="github_read",
                name="Read Repository Metadata & Code",
                description="Allows inspecting repositories, issues, and PRs.",
                enabled=True,
                required=True,
            )
        )

    def setup_tools(self) -> None:
        self.add_tool(
            PluginToolSchema(
                name="search_repositories",
                description="Searches GitHub repositories by name, language, or topic.",
                parameters=[
                    PluginToolParameter(name="query", type="string", description="Repository search keywords.", required=True),
                ],
                required_permission="github_read",
            )
        )

    def execute(self, tool_name: str, params: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        valid, err = self.validate_tool_call(tool_name, params)
        if not valid:
            return {"success": False, "error": err, "summary": f"Failed: {err}"}
        query = params.get("query", "")
        return {
            "success": True,
            "summary": f"GitHub connected: Searching repos for '{query}'.",
            "data": {"query": query, "status": "active_integration"},
        }


class GoogleDrivePlugin(BasePlugin):
    def __init__(self):
        super().__init__(
            id="google_drive",
            name="Google Drive",
            description="Find documents, spreadsheets, slides, and shared folders stored across your Google Drive cloud workspace.",
            category="Productivity",
            icon="📁",
            icon_bg="linear-gradient(135deg, #fbbc04, #ea4335)",
            version="1.0.0",
            author="Google Workspace",
            tags=["Drive", "Cloud", "Docs", "Sheets", "Storage"],
            requires_auth=True,
            is_connected=False,
            is_enabled=False,
        )

    def setup_permissions(self) -> None:
        self.add_permission(
            PluginPermission(
                id="drive_read",
                name="Read Drive File Metadata",
                description="Allows finding and reading document contents.",
                enabled=True,
                required=True,
            )
        )

    def setup_tools(self) -> None:
        self.add_tool(
            PluginToolSchema(
                name="search_drive",
                description="Searches Google Drive for files and folders by name or content.",
                parameters=[
                    PluginToolParameter(name="filename", type="string", description="Name or keywords of the file.", required=True),
                ],
                required_permission="drive_read",
            )
        )

    def execute(self, tool_name: str, params: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        valid, err = self.validate_tool_call(tool_name, params)
        if not valid:
            return {"success": False, "error": err, "summary": f"Failed: {err}"}
        fn = params.get("filename", "")
        return {
            "success": True,
            "summary": f"Google Drive connected: Searching for '{fn}'.",
            "data": {"filename": fn, "status": "active_integration"},
        }


class OutlookPlugin(BasePlugin):
    def __init__(self):
        super().__init__(
            id="outlook",
            name="Microsoft Outlook",
            description="Access your Microsoft 365 and Outlook corporate inbox, view flagged emails, and manage correspondence.",
            category="Productivity",
            icon="📬",
            icon_bg="linear-gradient(135deg, #0078d4, #005a9e)",
            version="1.0.0",
            author="Microsoft Corporation",
            tags=["Outlook", "Microsoft 365", "Email", "Corporate"],
            requires_auth=True,
            is_connected=False,
            is_enabled=False,
        )

    def setup_permissions(self) -> None:
        self.add_permission(
            PluginPermission(
                id="outlook_read",
                name="Read Outlook Mailbox",
                description="Allows querying inbox folders and email messages.",
                enabled=True,
                required=True,
            )
        )

    def setup_tools(self) -> None:
        self.add_tool(
            PluginToolSchema(
                name="search_outlook_messages",
                description="Searches Outlook mailbox for messages.",
                parameters=[
                    PluginToolParameter(name="query", type="string", description="Search query string.", required=True),
                ],
                required_permission="outlook_read",
            )
        )

    def execute(self, tool_name: str, params: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        valid, err = self.validate_tool_call(tool_name, params)
        if not valid:
            return {"success": False, "error": err, "summary": f"Failed: {err}"}
        q = params.get("query", "")
        return {"success": True, "summary": f"Outlook connected: Queried messages for '{q}'.", "data": {"query": q}}


class GoogleCalendarPlugin(BasePlugin):
    def __init__(self):
        super().__init__(
            id="calendar",
            name="Google Calendar",
            description="View your agenda, schedule AI-assisted calendar events, check meeting conflicts, and organize time.",
            category="Productivity",
            icon="📅",
            icon_bg="linear-gradient(135deg, #4285f4, #1a73e8)",
            version="1.0.0",
            author="Google Workspace",
            tags=["Calendar", "Meetings", "Schedule", "Time"],
            requires_auth=True,
            is_connected=False,
            is_enabled=False,
        )

    def setup_permissions(self) -> None:
        self.add_permission(
            PluginPermission(
                id="calendar_read",
                name="View Calendar Events & Schedule",
                description="Allows checking upcoming events and busy slots.",
                enabled=True,
                required=True,
            )
        )

    def setup_tools(self) -> None:
        self.add_tool(
            PluginToolSchema(
                name="list_upcoming_events",
                description="Lists upcoming calendar events for today or this week.",
                parameters=[
                    PluginToolParameter(name="days_ahead", type="integer", description="Number of days to check (default 7).", required=False, default=7),
                ],
                required_permission="calendar_read",
            )
        )

    def execute(self, tool_name: str, params: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        valid, err = self.validate_tool_call(tool_name, params)
        if not valid:
            return {"success": False, "error": err, "summary": f"Failed: {err}"}
        days = params.get("days_ahead", 7)
        return {"success": True, "summary": f"Calendar connected: Checked agenda for next {days} days.", "data": {"days": days}}


class SlackPlugin(BasePlugin):
    def __init__(self):
        super().__init__(
            id="slack",
            name="Slack",
            description="Collaborate with your team, search Slack channels, and send AI alerts directly to workspaces.",
            category="Productivity",
            icon="💬",
            icon_bg="linear-gradient(135deg, #4a154b, #611f69)",
            version="1.0.0",
            author="Slack Technologies",
            tags=["Slack", "Chat", "Messaging", "Team"],
            requires_auth=True,
            is_connected=False,
            is_enabled=False,
        )

    def setup_permissions(self) -> None:
        self.add_permission(
            PluginPermission(
                id="slack_send",
                name="Post Messages to Slack Channels",
                description="Allows posting summaries and alerts to authorized channels.",
                enabled=True,
                required=True,
            )
        )

    def setup_tools(self) -> None:
        self.add_tool(
            PluginToolSchema(
                name="send_slack_message",
                description="Sends a notification message to a specified Slack channel.",
                parameters=[
                    PluginToolParameter(name="channel", type="string", description="Slack channel name (e.g. '#general').", required=True),
                    PluginToolParameter(name="text", type="string", description="Message content to post.", required=True),
                ],
                required_permission="slack_send",
            )
        )

    def execute(self, tool_name: str, params: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        valid, err = self.validate_tool_call(tool_name, params)
        if not valid:
            return {"success": False, "error": err, "summary": f"Failed: {err}"}
        ch = params.get("channel", "")
        return {"success": True, "summary": f"Slack connected: Dispatched message to {ch}.", "data": {"channel": ch}}


class DropboxPlugin(BasePlugin):
    def __init__(self):
        super().__init__(
            id="dropbox",
            name="Dropbox",
            description="Seamlessly browse, search, and link cloud files stored across your Dropbox personal and team folders.",
            category="Cloud",
            icon="📦",
            icon_bg="linear-gradient(135deg, #0061ff, #004ecc)",
            version="1.0.0",
            author="Dropbox Inc.",
            tags=["Dropbox", "Cloud", "Files", "Backup"],
            requires_auth=True,
            is_connected=False,
            is_enabled=False,
        )

    def setup_permissions(self) -> None:
        self.add_permission(
            PluginPermission(
                id="dropbox_read",
                name="Browse Dropbox Files",
                description="Allows searching file names and metadata in Dropbox.",
                enabled=True,
                required=True,
            )
        )

    def setup_tools(self) -> None:
        self.add_tool(
            PluginToolSchema(
                name="search_dropbox_files",
                description="Searches Dropbox folders for files matching query.",
                parameters=[
                    PluginToolParameter(name="query", type="string", description="File name or extension search keyword.", required=True),
                ],
                required_permission="dropbox_read",
            )
        )

    def execute(self, tool_name: str, params: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        valid, err = self.validate_tool_call(tool_name, params)
        if not valid:
            return {"success": False, "error": err, "summary": f"Failed: {err}"}
        q = params.get("query", "")
        return {"success": True, "summary": f"Dropbox connected: Searched files for '{q}'.", "data": {"query": q}}


class NotionPlugin(BasePlugin):
    def __init__(self):
        super().__init__(
            id="notion",
            name="Notion",
            description="Search your connected Notion workspace, fetch notes, review documentation pages, and create new knowledge entries.",
            category="Productivity",
            icon="📓",
            icon_bg="linear-gradient(135deg, #191919, #000000)",
            version="1.0.0",
            author="Notion Labs",
            tags=["Notion", "Notes", "Wiki", "Docs", "Workspace"],
            requires_auth=True,
            is_connected=False,
            is_enabled=False,
        )

    def setup_permissions(self) -> None:
        self.add_permission(
            PluginPermission(
                id="notion_read",
                name="Read Workspace Pages & Databases",
                description="Allows searching and viewing documents in Notion.",
                enabled=True,
                required=True,
            )
        )

    def setup_tools(self) -> None:
        self.add_tool(
            PluginToolSchema(
                name="search_notion_pages",
                description="Searches Notion workspace for pages, databases, and notes.",
                parameters=[
                    PluginToolParameter(name="query", type="string", description="Search query.", required=True),
                ],
                required_permission="notion_read",
            )
        )

    def execute(self, tool_name: str, params: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        valid, err = self.validate_tool_call(tool_name, params)
        if not valid:
            return {"success": False, "error": err, "summary": f"Failed: {err}"}
        q = params.get("query", "")
        return {"success": True, "summary": f"Notion connected: Found workspace pages for '{q}'.", "data": {"query": q}}


class DatabasesPlugin(BasePlugin):
    def __init__(self):
        super().__init__(
            id="databases",
            name="Databases & SQL Studio",
            description="Safely inspect database schemas, generate SQL queries, and execute read-only analysis across PostgreSQL, Azure SQL, and MySQL.",
            category="Developer Tools",
            icon="🗄️",
            icon_bg="linear-gradient(135deg, #336791, #1e3c5a)",
            version="1.0.0",
            author="Cloud Database Systems",
            tags=["SQL", "PostgreSQL", "Azure SQL", "MySQL", "Developer", "Cloud"],
            requires_auth=True,
            is_connected=False,
            is_enabled=False,
        )

    def setup_permissions(self) -> None:
        self.add_permission(
            PluginPermission(
                id="sql_readonly",
                name="Execute Read-Only SELECT Queries",
                description="Allows running safe SELECT and schema inspection queries (Mutations & DDL strictly blocked).",
                enabled=True,
                required=True,
            )
        )

    def setup_tools(self) -> None:
        self.add_tool(
            PluginToolSchema(
                name="inspect_db_schema",
                description="Inspects tables, column types, and foreign key relations in the connected database.",
                parameters=[
                    PluginToolParameter(name="database_type", type="string", description="Database engine ('postgresql', 'azuresql', 'mysql').", required=False, default="azuresql"),
                ],
                required_permission="sql_readonly",
            )
        )

    def execute(self, tool_name: str, params: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        valid, err = self.validate_tool_call(tool_name, params)
        if not valid:
            return {"success": False, "error": err, "summary": f"Failed: {err}"}
        db_type = params.get("database_type", "azuresql")
        return {
            "success": True,
            "summary": f"Database Studio connected: Schema inspection ready for '{db_type}'.",
            "data": {"engine": db_type, "status": "active_integration"},
        }

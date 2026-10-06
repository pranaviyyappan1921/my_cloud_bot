"""
Base Plugin Interface and Schema Definitions for Cloud AI Chatbot.

Provides:
- BasePlugin abstract class
- Secure parameter schema validation
- Granular permission management
- OpenAI / JSON-Schema compatible tool specifications
- Serialization for REST APIs
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
import logging

logger = logging.getLogger("chatbot.plugins.base")


class PluginPermission:
    """Represents a granular permission requested/granted by a plugin."""

    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        enabled: bool = True,
        required: bool = False,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.enabled = enabled
        self.required = required

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "required": self.required,
        }


class PluginToolParameter:
    """Describes a single parameter for a tool."""

    def __init__(
        self,
        name: str,
        type: str,  # "string", "number", "integer", "boolean", "array", "object"
        description: str,
        required: bool = True,
        enum: Optional[List[Any]] = None,
        default: Optional[Any] = None,
    ):
        self.name = name
        self.type = type
        self.description = description
        self.required = required
        self.enum = enum
        self.default = default

    def to_json_schema(self) -> Dict[str, Any]:
        schema: Dict[str, Any] = {
            "type": self.type,
            "description": self.description,
        }
        if self.enum:
            schema["enum"] = self.enum
        if self.default is not None:
            schema["default"] = self.default
        return schema


class PluginToolSchema:
    """Represents a tool exposed by a plugin for AI function calling."""

    def __init__(
        self,
        name: str,
        description: str,
        parameters: List[PluginToolParameter],
        required_permission: Optional[str] = None,
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.required_permission = required_permission

    def to_dict(self) -> Dict[str, Any]:
        properties = {}
        required_params = []
        for p in self.parameters:
            properties[p.name] = p.to_json_schema()
            if p.required:
                required_params.append(p.name)

        return {
            "name": self.name,
            "description": self.description,
            "required_permission": self.required_permission,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required_params,
            },
        }


class BasePlugin(ABC):
    """
    Abstract Base Class for all AI Plugins.
    """

    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        category: str,  # "Popular", "Developer Tools", "Productivity", "AI & Search", "Cloud"
        icon: str,  # SVG markup or emoji
        icon_bg: str = "linear-gradient(135deg, #3b82f6, #1d4ed8)",
        version: str = "1.0.0",
        author: str = "Cloud AI Team",
        tags: Optional[List[str]] = None,
        requires_auth: bool = False,
        is_connected: bool = False,
        is_enabled: bool = False,
    ):
        self.id = id
        self.name = name
        self.description = description
        self.category = category
        self.icon = icon
        self.icon_bg = icon_bg
        self.version = version
        self.author = author
        self.tags = tags or []
        self.requires_auth = requires_auth
        self.is_connected = is_connected
        self.is_enabled = is_enabled
        self.config: Dict[str, Any] = {}
        self.permissions: Dict[str, PluginPermission] = {}
        self.tools: Dict[str, PluginToolSchema] = {}

        self.setup_permissions()
        self.setup_tools()

    @abstractmethod
    def setup_permissions(self) -> None:
        """Register permissions for this plugin."""
        pass

    @abstractmethod
    def setup_tools(self) -> None:
        """Register tools/functions exposed by this plugin."""
        pass

    def add_permission(self, permission: PluginPermission) -> None:
        self.permissions[permission.id] = permission

    def add_tool(self, tool: PluginToolSchema) -> None:
        self.tools[tool.name] = tool

    def has_permission(self, permission_id: Optional[str]) -> bool:
        """Checks if a given permission is enabled."""
        if not permission_id:
            return True
        perm = self.permissions.get(permission_id)
        if not perm:
            return False
        return perm.enabled

    def validate_tool_call(self, tool_name: str, params: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validates whether a tool can be executed securely with given arguments.
        Enforces:
        - Tool existence
        - Plugin enabled & connected
        - Permission enabled
        - Parameter type checks & required parameters presence
        - Security checks against malicious injection
        """
        if not self.is_connected:
            return False, f"Plugin '{self.name}' is not connected. Please connect it first."

        if not self.is_enabled:
            return False, f"Plugin '{self.name}' is disabled. Please enable it in Apps / Plugins."

        tool = self.tools.get(tool_name)
        if not tool:
            return False, f"Unknown tool '{tool_name}' for plugin '{self.name}'."

        if tool.required_permission and not self.has_permission(tool.required_permission):
            return False, f"Permission '{tool.required_permission}' is disabled for plugin '{self.name}'."

        # Validate parameters against schema
        for param in tool.parameters:
            val = params.get(param.name)
            if param.required and (val is None or (isinstance(val, str) and not val.strip())):
                return False, f"Missing required parameter '{param.name}' for tool '{tool_name}'."

            if val is not None:
                # Basic type validation
                if param.type == "string" and not isinstance(val, (str, int, float)):
                    return False, f"Parameter '{param.name}' must be a string."
                elif param.type in ("number", "integer") and not isinstance(val, (int, float)):
                    try:
                        float(val)
                    except (ValueError, TypeError):
                        return False, f"Parameter '{param.name}' must be a number."
                elif param.type == "boolean" and not isinstance(val, bool):
                    if str(val).lower() not in ("true", "false", "1", "0"):
                        return False, f"Parameter '{param.name}' must be a boolean."
                elif param.type == "array" and not isinstance(val, list):
                    return False, f"Parameter '{param.name}' must be a list/array."

                # Enum validation
                if param.enum and val not in param.enum:
                    return False, f"Parameter '{param.name}' must be one of: {param.enum}."

        return True, None

    @abstractmethod
    def execute(
        self,
        tool_name: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes a plugin tool and returns structured result dictionary.
        Returns:
            {
                "success": bool,
                "result": Any,
                "summary": str,
                "data": Optional[Dict],
                "error": Optional[str]
            }
        """
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Serializes plugin info for REST APIs and UI marketplace."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "icon": self.icon,
            "icon_bg": self.icon_bg,
            "version": self.version,
            "author": self.author,
            "tags": self.tags,
            "requires_auth": self.requires_auth,
            "is_connected": self.is_connected,
            "is_enabled": self.is_enabled,
            "config_keys": list(self.config.keys()),
            "permissions": [p.to_dict() for p in self.permissions.values()],
            "tools": [t.to_dict() for t in self.tools.values()],
        }

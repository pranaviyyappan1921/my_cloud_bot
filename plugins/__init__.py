"""
Plugins module for Cloud AI Chatbot.
Provides modular, extensible, secure AI plugin architecture.
"""

from .base_plugin import BasePlugin, PluginPermission, PluginToolParameter, PluginToolSchema
from .plugin_manager import PluginManager, plugin_manager

__all__ = [
    "BasePlugin",
    "PluginPermission",
    "PluginToolParameter",
    "PluginToolSchema",
    "PluginManager",
    "plugin_manager",
]

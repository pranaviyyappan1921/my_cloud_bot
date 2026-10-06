"""
Azure Blob Storage Integration Plugin for Cloud AI Chatbot.

Reuses existing storage utilities in utils/azure_blob.py to provide:
- Real-time cloud storage container health checks
- Listing blobs, backups, and user document artifacts
- Inspecting cloud file metadata and availability
"""

import logging
from typing import Dict, Any, Optional
from .base_plugin import BasePlugin, PluginPermission, PluginToolParameter, PluginToolSchema
from utils.azure_blob import list_files as az_list_files, check_connection as az_check_connection, blob_exists as az_blob_exists

logger = logging.getLogger("chatbot.plugins.azure_blob")


class AzureBlobPlugin(BasePlugin):
    """
    Microsoft Azure Blob Storage integration plugin.
    """

    def __init__(self):
        super().__init__(
            id="azure_blob",
            name="Azure Blob Storage",
            description="Manage, inspect, and monitor Microsoft Azure Blob Storage containers, backups, and cloud document repositories.",
            category="Cloud",
            icon="☁️",
            icon_bg="linear-gradient(135deg, #0078d4, #005a9e)",
            version="1.1.0",
            author="Microsoft Azure & Cloud AI",
            tags=["Azure", "Cloud", "Blob Storage", "Backups", "Enterprise"],
            requires_auth=False,
            is_connected=True,
            is_enabled=True,
        )

    def setup_permissions(self) -> None:
        self.add_permission(
            PluginPermission(
                id="storage_read",
                name="Read Azure Blob Metadata & List Files",
                description="Allows listing cloud blobs and checking storage container status.",
                enabled=True,
                required=True,
            )
        )
        self.add_permission(
            PluginPermission(
                id="storage_health",
                name="Perform Health & Connection Checks",
                description="Allows checking connectivity against Microsoft Azure Storage endpoints.",
                enabled=True,
                required=False,
            )
        )

    def setup_tools(self) -> None:
        # Tool 1: List Blobs
        self.add_tool(
            PluginToolSchema(
                name="list_storage_blobs",
                description="Lists all files and blobs currently stored in the configured Microsoft Azure Blob Storage container.",
                parameters=[],
                required_permission="storage_read",
            )
        )

        # Tool 2: Check Connection Status
        self.add_tool(
            PluginToolSchema(
                name="check_storage_status",
                description="Checks the health and connectivity status of the Microsoft Azure Blob Storage service.",
                parameters=[],
                required_permission="storage_health",
            )
        )

        # Tool 3: Get Blob Info
        self.add_tool(
            PluginToolSchema(
                name="get_blob_info",
                description="Checks if a specific blob exists in Azure Blob Storage and returns its availability status.",
                parameters=[
                    PluginToolParameter(
                        name="blob_name",
                        type="string",
                        description="The exact name or key of the blob in the Azure container.",
                        required=True,
                    )
                ],
                required_permission="storage_read",
            )
        )

    def execute(
        self,
        tool_name: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        valid, err = self.validate_tool_call(tool_name, params)
        if not valid:
            return {"success": False, "error": err, "summary": f"Failed: {err}"}

        if tool_name == "list_storage_blobs":
            return self._execute_list_blobs()
        elif tool_name == "check_storage_status":
            return self._execute_check_status()
        elif tool_name == "get_blob_info":
            blob_name = str(params.get("blob_name", "")).strip()
            return self._execute_get_blob_info(blob_name)
        else:
            return {"success": False, "error": f"Unknown tool '{tool_name}'.", "summary": "Tool not found."}

    def _execute_list_blobs(self) -> Dict[str, Any]:
        try:
            blobs = az_list_files()
            summary = f"Azure Blob Storage has {len(blobs)} item(s) in container."
            return {
                "success": True,
                "blobs": blobs,
                "count": len(blobs),
                "summary": summary,
                "data": {"blobs": blobs, "count": len(blobs)},
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to list Azure blobs: {str(e)}",
                "summary": f"Azure Storage error: {str(e)}",
            }

    def _execute_check_status(self) -> Dict[str, Any]:
        try:
            connected = az_check_connection()
            status_str = "Online & Connected" if connected else "Disconnected / Unreachable"
            return {
                "success": True,
                "connected": connected,
                "status": status_str,
                "provider": "Microsoft Azure Blob Storage",
                "summary": f"Azure Blob Storage: {status_str}",
                "data": {"connected": connected, "status": status_str},
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Azure storage connection check error: {str(e)}",
                "summary": f"Connection check failed: {str(e)}",
            }

    def _execute_get_blob_info(self, blob_name: str) -> Dict[str, Any]:
        if not blob_name:
            return {"success": False, "error": "Blob name is required.", "summary": "Empty blob name"}

        try:
            exists = az_blob_exists(blob_name)
            summary = f"Blob '{blob_name}': {'Exists in storage' if exists else 'Not found'}"
            return {
                "success": True,
                "blob_name": blob_name,
                "exists": exists,
                "summary": summary,
                "data": {"blob_name": blob_name, "exists": exists},
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Could not inspect blob '{blob_name}': {str(e)}",
                "summary": f"Inspection failed: {str(e)}",
            }

"""
File Analysis & Document Intelligence Plugin for Cloud AI Chatbot.

Reuses existing file processing logic from utils/file_processor.py to provide:
- Deep document Q&A and structured executive summaries
- Plaintext and table extraction for PDF, DOCX, and TXT files
- Uploaded workspace documents listing
"""

import os
import glob
import logging
from typing import Dict, Any, Optional, List
from .base_plugin import BasePlugin, PluginPermission, PluginToolParameter, PluginToolSchema
from utils.file_processor import extract_text_from_file, generate_document_analysis_report

logger = logging.getLogger("chatbot.plugins.file_analysis")


class FileAnalysisPlugin(BasePlugin):
    """
    Intelligent Document Parsing and Content Analysis plugin.
    """

    def __init__(self, uploads_dir: Optional[str] = None):
        self.uploads_dir = uploads_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
        super().__init__(
            id="file_analysis",
            name="Document & File Analysis",
            description="Deep analysis, executive summaries, table extraction, and Q&A across uploaded PDF, Word (.docx), and text documents.",
            category="Productivity",
            icon="📄",
            icon_bg="linear-gradient(135deg, #8b5cf6, #6d28d9)",
            version="1.4.0",
            author="Cloud AI Doc Systems",
            tags=["Documents", "PDF", "Word", "Analysis", "Summary", "Popular"],
            requires_auth=False,
            is_connected=True,
            is_enabled=True,
        )

    def setup_permissions(self) -> None:
        self.add_permission(
            PluginPermission(
                id="doc_read",
                name="Read Uploaded Documents",
                description="Allows the plugin to read files stored in the active session upload space.",
                enabled=True,
                required=True,
            )
        )
        self.add_permission(
            PluginPermission(
                id="doc_summary",
                name="Generate Structured Analysis Reports",
                description="Allows building executive summaries, key findings, and analytical reports.",
                enabled=True,
                required=False,
            )
        )

    def setup_tools(self) -> None:
        # Tool 1: Analyze Document
        self.add_tool(
            PluginToolSchema(
                name="analyze_document",
                description="Performs deep structured analysis of an uploaded document (PDF, Word, or TXT), answering specific questions or generating executive summaries.",
                parameters=[
                    PluginToolParameter(
                        name="file_name",
                        type="string",
                        description="Filename or path of the uploaded document (e.g. 'report.pdf', 'contract.docx').",
                        required=True,
                    ),
                    PluginToolParameter(
                        name="query",
                        type="string",
                        description="User question or focus area for analysis (e.g. 'Summarize key risks and action items').",
                        required=False,
                        default="Provide a comprehensive summary and key takeaways.",
                    ),
                ],
                required_permission="doc_summary",
            )
        )

        # Tool 2: Extract Document Text
        self.add_tool(
            PluginToolSchema(
                name="extract_document_text",
                description="Extracts raw text content and metadata from an uploaded PDF, DOCX, or TXT document.",
                parameters=[
                    PluginToolParameter(
                        name="file_name",
                        type="string",
                        description="Name of the file to extract text from.",
                        required=True,
                    ),
                    PluginToolParameter(
                        name="max_chars",
                        type="integer",
                        description="Maximum number of characters to return (default 10,000).",
                        required=False,
                        default=10000,
                    ),
                ],
                required_permission="doc_read",
            )
        )

        # Tool 3: List Uploaded Documents
        self.add_tool(
            PluginToolSchema(
                name="list_uploaded_files",
                description="Lists all currently uploaded document files available for analysis in the current environment.",
                parameters=[],
                required_permission="doc_read",
            )
        )

    def _resolve_file_path(self, file_name: str) -> Optional[str]:
        """Safely locates file path inside uploads folder to prevent directory traversal."""
        clean_name = os.path.basename(file_name)
        direct_path = os.path.join(self.uploads_dir, clean_name)
        if os.path.exists(direct_path):
            return direct_path

        # Search for uuid prefixed match e.g. 1a2b3c4d_report.pdf
        pattern = os.path.join(self.uploads_dir, f"*_{clean_name}")
        matches = glob.glob(pattern)
        if matches:
            return matches[0]

        # Search case-insensitive or partial match
        for f in os.listdir(self.uploads_dir):
            if clean_name.lower() in f.lower():
                return os.path.join(self.uploads_dir, f)

        return None

    def execute(
        self,
        tool_name: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        valid, err = self.validate_tool_call(tool_name, params)
        if not valid:
            return {"success": False, "error": err, "summary": f"Failed: {err}"}

        if tool_name == "analyze_document":
            file_name = str(params.get("file_name", "")).strip()
            query = str(params.get("query", "Provide a comprehensive summary and key takeaways.")).strip()
            return self._execute_analyze(file_name, query)
        elif tool_name == "extract_document_text":
            file_name = str(params.get("file_name", "")).strip()
            max_chars = int(params.get("max_chars", 10000) or 10000)
            return self._execute_extract(file_name, max_chars)
        elif tool_name == "list_uploaded_files":
            return self._execute_list_files()
        else:
            return {"success": False, "error": f"Unknown tool '{tool_name}'.", "summary": "Tool not found."}

    def _execute_analyze(self, file_name: str, query: str) -> Dict[str, Any]:
        file_path = self._resolve_file_path(file_name)
        if not file_path:
            return {
                "success": False,
                "error": f"Document '{file_name}' not found in upload repository. Please attach or upload the file first.",
                "summary": "Document not found",
            }

        try:
            text = extract_text_from_file(file_path)
            report = generate_document_analysis_report(os.path.basename(file_path), text, query)
            return {
                "success": True,
                "file_name": os.path.basename(file_path),
                "query": query,
                "total_chars": len(text),
                "report": report,
                "summary": f"Analyzed '{os.path.basename(file_path)}' ({len(text)} chars)",
                "data": {"file_name": os.path.basename(file_path), "report": report},
            }
        except Exception as e:
            return {"success": False, "error": f"Document analysis failed: {str(e)}", "summary": f"Analysis error: {str(e)}"}

    def _execute_extract(self, file_name: str, max_chars: int) -> Dict[str, Any]:
        file_path = self._resolve_file_path(file_name)
        if not file_path:
            return {
                "success": False,
                "error": f"File '{file_name}' was not found in uploads directory.",
                "summary": "File not found",
            }

        try:
            text = extract_text_from_file(file_path)
            truncated = text[:max_chars]
            return {
                "success": True,
                "file_name": os.path.basename(file_path),
                "total_chars": len(text),
                "extracted_length": len(truncated),
                "is_truncated": len(text) > max_chars,
                "text": truncated,
                "summary": f"Extracted {len(truncated)} characters from '{os.path.basename(file_path)}'",
                "data": {"file_name": os.path.basename(file_path), "text": truncated},
            }
        except Exception as e:
            return {"success": False, "error": f"Failed to extract document text: {str(e)}", "summary": f"Extraction error: {str(e)}"}

    def _execute_list_files(self) -> Dict[str, Any]:
        try:
            if not os.path.exists(self.uploads_dir):
                return {"success": True, "files": [], "count": 0, "summary": "No uploaded files found."}

            files_info = []
            for entry in os.listdir(self.uploads_dir):
                full_p = os.path.join(self.uploads_dir, entry)
                if os.path.isfile(full_p):
                    # Clean display name
                    clean_name = entry
                    if "_" in entry and len(entry.split("_")[0]) == 8:
                        clean_name = "_".join(entry.split("_")[1:])
                    files_info.append({
                        "name": clean_name,
                        "stored_name": entry,
                        "size_bytes": os.path.getsize(full_p),
                        "size_kb": round(os.path.getsize(full_p) / 1024, 1),
                    })

            summary = f"Found {len(files_info)} uploaded document(s)" if files_info else "No uploaded documents available."
            return {
                "success": True,
                "files": files_info,
                "count": len(files_info),
                "summary": summary,
                "data": {"files": files_info},
            }
        except Exception as e:
            return {"success": False, "error": f"Could not list uploads: {str(e)}", "summary": f"Error: {str(e)}"}

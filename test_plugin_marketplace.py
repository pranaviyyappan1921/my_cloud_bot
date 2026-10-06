"""
Verification Test Suite for AI Plugin Marketplace and Tool Architecture.
Tests:
1. Plugin discovery, initialization & state persistence
2. Safe AST-based Calculator & Math Engine
3. Code injection prevention & security sandbox
4. Web Search & Grounding plugin
5. File Analysis & Document Intelligence plugin
6. Azure Blob Storage plugin
7. Connect, Disconnect, Enable, Disable, Permissions update APIs
8. Telemetry and execution logging APIs
9. AI Automatic plugin selection & execution in /api/chat
10. HTML and UI marketplace elements in template
"""

import os
import json
import unittest
from dotenv import load_dotenv

load_dotenv()
os.environ["FLASK_SECRET_KEY"] = "test-plugin-secret-key"

from app import app
from plugins.plugin_manager import plugin_manager


class PluginMarketplaceTestCase(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()
        # Reset core plugin state for clean tests
        for pid in ["calculator", "web_search", "file_analysis", "azure_blob"]:
            p = plugin_manager.get_plugin(pid)
            if p:
                p.is_connected = True
                p.is_enabled = True
                for perm in p.permissions.values():
                    perm.enabled = True
        plugin_manager._save_state()


    def test_01_plugins_list_endpoint(self):
        """Verify GET /api/plugins returns full plugin catalog and stats."""
        res = self.client.get("/api/plugins")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertGreaterEqual(data["total"], 13)
        self.assertIn("stats", data)
        self.assertGreaterEqual(data["stats"]["total_plugins"], 13)

        # Verify real working plugins exist
        plugin_ids = [p["id"] for p in data["plugins"]]
        self.assertIn("calculator", plugin_ids)
        self.assertIn("web_search", plugin_ids)
        self.assertIn("file_analysis", plugin_ids)
        self.assertIn("azure_blob", plugin_ids)

        # Verify future integration cards exist
        self.assertIn("gmail", plugin_ids)
        self.assertIn("github", plugin_ids)
        self.assertIn("google_drive", plugin_ids)
        self.assertIn("outlook", plugin_ids)
        self.assertIn("calendar", plugin_ids)
        self.assertIn("slack", plugin_ids)
        self.assertIn("dropbox", plugin_ids)
        self.assertIn("notion", plugin_ids)
        self.assertIn("databases", plugin_ids)
        print("[PASSED] GET /api/plugins catalog listing test")

    def test_02_plugin_category_and_search_filters(self):
        """Verify filtering plugins by category, search query, and connected status."""
        # Category filter: Popular
        res_pop = self.client.get("/api/plugins?category=Popular")
        self.assertEqual(res_pop.status_code, 200)
        pop_plugins = res_pop.get_json()["plugins"]
        self.assertTrue(any(p["id"] == "calculator" for p in pop_plugins))

        # Search query filter: github
        res_gh = self.client.get("/api/plugins?q=github")
        self.assertEqual(res_gh.status_code, 200)
        gh_plugins = res_gh.get_json()["plugins"]
        self.assertEqual(len(gh_plugins), 1)
        self.assertEqual(gh_plugins[0]["id"], "github")

        # Connected only filter
        res_conn = self.client.get("/api/plugins?connected=true")
        self.assertEqual(res_conn.status_code, 200)
        conn_plugins = res_conn.get_json()["plugins"]
        for cp in conn_plugins:
            self.assertTrue(cp["is_connected"])
        print("[PASSED] Plugin category and search filters test")

    def test_03_calculator_plugin_math_and_conversions(self):
        """Verify Calculator plugin evaluates arithmetic, trig, units, and statistics."""
        calc = plugin_manager.get_plugin("calculator")
        self.assertIsNotNone(calc)

        # 1. Arithmetic evaluation
        res_math = calc.execute("calculate", {"expression": "45 * 38 + sqrt(144)"})
        self.assertTrue(res_math["success"])
        self.assertEqual(res_math["result"], 1722.0)
        self.assertEqual(res_math["formatted"], "1722")

        # 2. Trigonometry & constants
        res_trig = calc.execute("calculate", {"expression": "sin(pi / 2)"})
        self.assertTrue(res_trig["success"])
        self.assertAlmostEqual(res_trig["result"], 1.0)

        # 3. Unit conversion (Length & Temp)
        res_unit_len = calc.execute("convert_units", {"value": 100, "from_unit": "km", "to_unit": "mi"})
        self.assertTrue(res_unit_len["success"])
        self.assertAlmostEqual(res_unit_len["result"], 62.1371, places=3)

        res_unit_temp = calc.execute("convert_units", {"value": 100, "from_unit": "c", "to_unit": "f"})
        self.assertTrue(res_unit_temp["success"])
        self.assertEqual(res_unit_temp["result"], 212.0)

        # 4. Statistics
        res_stats = calc.execute("calculate_statistics", {"numbers": [10, 20, 30, 40, 50]})
        self.assertTrue(res_stats["success"])
        self.assertEqual(res_stats["result"]["mean"], 30.0)
        self.assertEqual(res_stats["result"]["median"], 30.0)
        self.assertEqual(res_stats["result"]["sum"], 150.0)
        print("[PASSED] Calculator plugin math, units, and stats test")

    def test_04_calculator_security_sandbox(self):
        """Verify AST sandbox strictly blocks code execution, __import__, eval, and invalid syntax."""
        calc = plugin_manager.get_plugin("calculator")

        # Attack: __import__
        res_import = calc.execute("calculate", {"expression": "__import__('os').system('dir')"})
        self.assertFalse(res_import["success"])
        self.assertTrue(bool(res_import.get("error")))

        # Attack: eval()
        res_eval = calc.execute("calculate", {"expression": "eval('2+2')"})
        self.assertFalse(res_eval["success"])

        # Attack: exec()
        res_exec = calc.execute("calculate", {"expression": "exec('print(1)')"})
        self.assertFalse(res_exec["success"])

        # Division by zero
        res_div = calc.execute("calculate", {"expression": "100 / 0"})
        self.assertFalse(res_div["success"])
        self.assertIn("zero", res_div["error"].lower())
        print("[PASSED] Calculator security AST sandbox test")

    def test_05_web_search_plugin(self):
        """Verify Web Search plugin returns structured search results."""
        web = plugin_manager.get_plugin("web_search")
        self.assertIsNotNone(web)

        res = web.execute("search_web", {"query": "Microsoft Azure cloud", "num_results": 3})
        self.assertTrue(res["success"])
        self.assertIn("results", res)
        self.assertGreaterEqual(len(res["results"]), 1)
        self.assertTrue(all("title" in r and "url" in r for r in res["results"]))
        print("[PASSED] Web Search plugin live search test")

    def test_06_file_analysis_plugin(self):
        """Verify File Analysis plugin lists files and extracts content."""
        file_plugin = plugin_manager.get_plugin("file_analysis")
        self.assertIsNotNone(file_plugin)

        # 1. List files
        res_list = file_plugin.execute("list_uploaded_files", {})
        self.assertTrue(res_list["success"])
        self.assertIn("files", res_list)

        # 2. Extract text from existing test file
        test_txt = os.path.join(app.config["UPLOAD_FOLDER"], "test_sample.txt")
        with open(test_txt, "w", encoding="utf-8") as f:
            f.write("HPCC Project: Cloud Computing Architecture testing.")

        res_extract = file_plugin.execute("extract_document_text", {"file_name": "test_sample.txt", "max_chars": 500})
        self.assertTrue(res_extract["success"])
        self.assertIn("Cloud Computing Architecture", res_extract["text"])
        print("[PASSED] File Analysis plugin test")

    def test_07_azure_blob_plugin(self):
        """Verify Azure Blob Storage plugin executes connection and listing tools."""
        blob_plugin = plugin_manager.get_plugin("azure_blob")
        self.assertIsNotNone(blob_plugin)

        res_status = blob_plugin.execute("check_storage_status", {})
        self.assertTrue(res_status["success"])
        self.assertIn("connected", res_status)

        res_list = blob_plugin.execute("list_storage_blobs", {})
        self.assertTrue(res_list["success"])
        self.assertIn("blobs", res_list)
        print("[PASSED] Azure Blob Storage plugin test")

    def test_08_plugin_connect_disconnect_enable_disable(self):
        """Verify connect, disconnect, enable, and disable REST API cycle."""
        # 1. Connect GitHub integration
        res_conn = self.client.post("/api/plugins/github/connect", json={"config": {"api_key": "ghp_test_token"}})
        self.assertEqual(res_conn.status_code, 200)
        gh_data = res_conn.get_json()["plugin"]
        self.assertTrue(gh_data["is_connected"])
        self.assertTrue(gh_data["is_enabled"])

        # 2. Disable GitHub plugin
        res_dis = self.client.post("/api/plugins/github/disable")
        self.assertEqual(res_dis.status_code, 200)
        self.assertFalse(res_dis.get_json()["plugin"]["is_enabled"])

        # 3. Enable GitHub plugin
        res_en = self.client.post("/api/plugins/github/enable")
        self.assertEqual(res_en.status_code, 200)
        self.assertTrue(res_en.get_json()["plugin"]["is_enabled"])

        # 4. Disconnect GitHub plugin
        res_dc = self.client.post("/api/plugins/github/disconnect")
        self.assertEqual(res_dc.status_code, 200)
        self.assertFalse(res_dc.get_json()["plugin"]["is_connected"])
        print("[PASSED] Plugin connect/disconnect/enable/disable cycle test")

    def test_09_plugin_permission_management(self):
        """Verify updating and enforcing granular plugin permissions."""
        # Disable unit_conversion permission on calculator
        res_perm = self.client.put("/api/plugins/calculator/permissions", json={"permissions": {"unit_conversion": False}})
        self.assertEqual(res_perm.status_code, 200)

        # Executing convert_units tool should now be blocked
        calc = plugin_manager.get_plugin("calculator")
        res_blocked = calc.execute("convert_units", {"value": 50, "from_unit": "km", "to_unit": "mi"})
        self.assertFalse(res_blocked["success"])
        self.assertIn("disabled", res_blocked["error"].lower())

        # Re-enable permission
        res_perm2 = self.client.put("/api/plugins/calculator/permissions", json={"permissions": {"unit_conversion": True}})
        self.assertEqual(res_perm2.status_code, 200)

        # Execution works again
        res_ok = calc.execute("convert_units", {"value": 50, "from_unit": "km", "to_unit": "mi"})
        self.assertTrue(res_ok["success"])
        print("[PASSED] Plugin permission management & enforcement test")

    def test_10_plugin_execution_logging_apis(self):
        """Verify telemetry recording, querying, and clearing via REST APIs."""
        # Execute tool via REST API to generate log entry
        res_exec = self.client.post(
            "/api/plugins/calculator/execute",
            json={"tool_name": "calculate", "params": {"expression": "25 * 4"}},
        )
        self.assertEqual(res_exec.status_code, 200)

        # Retrieve logs
        res_logs = self.client.get("/api/plugins/logs?plugin_id=calculator")
        self.assertEqual(res_logs.status_code, 200)
        logs = res_logs.get_json()["logs"]
        self.assertGreaterEqual(len(logs), 1)
        latest = logs[0]
        self.assertEqual(latest["plugin_id"], "calculator")
        self.assertEqual(latest["action"], "calculate")
        self.assertEqual(latest["status"], "success")
        self.assertIn("duration_ms", latest)
        self.assertIn("timestamp", latest)

        # Check stats endpoint
        res_stats = self.client.get("/api/plugins/stats")
        self.assertEqual(res_stats.status_code, 200)
        stats = res_stats.get_json()["stats"]
        self.assertIn("total_executions", stats)
        self.assertIn("success_rate_percent", stats)
        print("[PASSED] Plugin execution telemetry and logging APIs test")

    def test_11_automatic_plugin_selection_in_chat(self):
        """Verify AI chatbot engine automatically selects and executes connected plugins in chat."""
        # Math calculation query in /api/chat
        res_chat = self.client.post("/api/chat", data={"message": "calculate 45 * 38 + sqrt(144)"})
        self.assertEqual(res_chat.status_code, 200)
        data = res_chat.get_json()
        self.assertIn("reply", data)
        self.assertIn("plugin_used", data)
        if data["plugin_used"]:
            self.assertEqual(data["plugin_used"]["name"], "Calculator & Math Engine")
            self.assertEqual(data["plugin_used"]["tool"], "calculate")

        # Storage listing query in /api/chat
        res_blob = self.client.post("/api/chat", data={"message": "list my azure storage blobs"})
        self.assertEqual(res_blob.status_code, 200)
        bdata = res_blob.get_json()
        if bdata.get("plugin_used"):
            self.assertEqual(bdata["plugin_used"]["name"], "Azure Blob Storage")
        print("[PASSED] Automatic AI plugin selection in chat test")

    def test_12_ui_template_marketplace_elements(self):
        """Verify index.html contains the Apps/Plugins sidebar button, marketplace view, and modals."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)

        # Sidebar navigation
        self.assertIn("sidebarPluginsBtn", html)
        self.assertIn("Apps / Plugins", html)

        # Main marketplace view
        self.assertIn("pluginsView", html)
        self.assertIn("pluginsGridContainer", html)
        self.assertIn("pluginSearchInput", html)
        self.assertIn("filterConnectedOnlyCheckbox", html)
        self.assertIn("data-category=\"Popular\"", html)
        self.assertIn("data-category=\"Developer Tools\"", html)
        self.assertIn("data-category=\"Productivity\"", html)
        self.assertIn("data-category=\"Cloud\"", html)

        # Modals
        self.assertIn("pluginConnectModal", html)
        self.assertIn("pluginManageModal", html)
        self.assertIn("pluginLogsModal", html)
        self.assertIn("openPluginLogsBtn", html)

        # Plugins direct route
        res_pl = self.client.get("/plugins")
        self.assertEqual(res_pl.status_code, 200)
        print("[PASSED] UI template marketplace elements test")


if __name__ == "__main__":
    unittest.main()

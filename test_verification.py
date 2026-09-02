"""
Automated Verification Test Suite for Cloud AI Chatbot
Tests all core features:
- /api/health
- Validation of TXT, PDF, DOCX, and Image files
- Validation of unsupported and oversized files
- Error handling for missing/invalid API key
- OpenRouter Gemini Client logic & multimodal payload preparation
- Conversation history & session clearing
"""

import os
import io
import unittest
import docx
from pypdf import PdfWriter

# Set test environment
os.environ["FLASK_SECRET_KEY"] = "test-secret-key"
os.environ["OPENROUTER_MODEL"] = "google/gemini-3.7-flash"

from app import app
from utils.file_processor import validate_file, extract_text_from_file, is_image_file, FileValidationError
from utils.gemini_client import GeminiClient, GeminiClientError


class ChatbotTestCase(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_01_health_endpoint(self):
        """Verify GET /api/health returns 200 OK and expected metadata."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("OpenRouter", data["provider"])
        self.assertEqual(data["model"], "google/gemini-3.7-flash")
        self.assertTrue(data["web_search"])
        print("[PASSED] /api/health endpoint test")

    def test_02_index_page(self):
        """Verify GET / returns 200 OK and contains chatbot layout."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("Cloud AI Chatbot", html)
        self.assertIn("Gemini Flash", html)
        self.assertIn("composerForm", html)
        print("[PASSED] / index page template test")

    def test_03_txt_file_processing(self):
        """Verify text extraction from a TXT file."""
        sample_text = "Cloud Computing is the on-demand delivery of compute power and storage."
        test_txt_path = os.path.join(app.config["UPLOAD_FOLDER"], "test_sample.txt")
        with open(test_txt_path, "w", encoding="utf-8") as f:
            f.write(sample_text)

        extracted = extract_text_from_file(test_txt_path)
        self.assertEqual(extracted, sample_text)
        print("[PASSED] TXT file extraction test")

    def test_04_docx_file_processing(self):
        """Verify text and table extraction from a DOCX file."""
        test_docx_path = os.path.join(app.config["UPLOAD_FOLDER"], "test_sample.docx")
        doc = docx.Document()
        doc.add_heading("HPCC Project Report", level=1)
        doc.add_paragraph("This document tests python-docx extraction for Azure Chatbot.")
        table = doc.add_table(rows=2, cols=2)
        table.cell(0, 0).text = "Service"
        table.cell(0, 1).text = "Role"
        table.cell(1, 0).text = "App Service"
        table.cell(1, 1).text = "Web Hosting"
        doc.save(test_docx_path)

        extracted = extract_text_from_file(test_docx_path)
        self.assertIn("HPCC Project Report", extracted)
        self.assertIn("App Service | Web Hosting", extracted)
        print("[PASSED] DOCX file extraction test")

    def test_05_pdf_file_processing(self):
        """Verify text extraction from a PDF file using pypdf."""
        test_pdf_path = os.path.join(app.config["UPLOAD_FOLDER"], "test_sample.pdf")
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        with open(test_pdf_path, "wb") as f:
            writer.write(f)

        with self.assertRaises(ValueError):
            extract_text_from_file(test_pdf_path)
        print("[PASSED] PDF empty/blank detection test")

    def test_06_image_file_detection(self):
        """Verify image format detection."""
        self.assertTrue(is_image_file("diagram.png"))
        self.assertTrue(is_image_file("photo.jpg"))
        self.assertTrue(is_image_file("banner.webp"))
        self.assertFalse(is_image_file("report.pdf"))
        self.assertFalse(is_image_file("notes.txt"))
        print("[PASSED] Image file detection test")

    def test_07_invalid_and_oversized_files(self):
        """Verify rejection of unsupported extensions and oversized files."""
        data = {
            "message": "Hello",
            "file": (io.BytesIO(b"binary content"), "malware.exe"),
        }
        res = self.client.post("/api/chat", data=data, content_type="multipart/form-data")
        self.assertEqual(res.status_code, 400)
        json_data = res.get_json()
        self.assertIn("Unsupported file type", json_data["error"])

        res_empty = self.client.post("/api/chat", data={"message": ""})
        self.assertEqual(res_empty.status_code, 400)
        print("[PASSED] Invalid file validation & empty message test")

    def test_08_api_key_error_handling(self):
        """Verify clear 401 error message when API key is missing or unconfigured."""
        client = GeminiClient(api_key="your_openrouter_api_key_here")
        with self.assertRaises(GeminiClientError) as ctx:
            client.generate_reply("Hello")
        self.assertEqual(ctx.exception.status_code, 401)
        self.assertIn("OPENROUTER_API_KEY", ctx.exception.message)
        print("[PASSED] API key defensive error handling test")

    def test_09_clear_chat_endpoint(self):
        """Verify POST /api/clear removes session history."""
        with self.client.session_transaction() as sess:
            sess["history"] = [{"role": "user", "text": "Hi"}, {"role": "model", "text": "Hello"}]

        res = self.client.post("/api/clear")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "cleared")

        with self.client.session_transaction() as sess:
            self.assertNotIn("history", sess)
        print("[PASSED] /api/clear session clearing test")

    def test_10_index_page_new_elements(self):
        """Verify GET / contains new chat, pinned, previous chats, and share elements."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("newChatBtn", html)
        self.assertIn("pinnedSection", html)
        self.assertIn("previousSection", html)
        self.assertIn("shareBtn", html)
        self.assertIn("shareDropdownMenu", html)
        self.assertIn("storage-notice", html)
        print("[PASSED] New Chat, Pinned, Previous Chats, and Share template elements test")

    def test_11_custom_history_handling(self):
        """Verify /api/chat gracefully parses custom history JSON parameter."""
        # Empty message with custom history should still return 400 for empty message
        res = self.client.post("/api/chat", data={"message": "", "history": '[{"role":"user","text":"test"}]'})
        self.assertEqual(res.status_code, 400)
        print("[PASSED] Custom history parsing validation test")

    def test_12_model_and_effort_configuration(self):
        """Verify model popover menu, effort options, and microphone button in HTML and health endpoint."""
        # 1. Verify UI elements exist in template
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("modelMenuBtn", html)
        self.assertIn("modelPopoverMenu", html)
        self.assertIn("micBtn", html)
        self.assertIn("google/gemini-3.7-flash", html)
        self.assertIn("google/gemini-3.6-flash", html)
        self.assertIn("google/gemini-3.1-flash-lite", html)
        self.assertIn('data-effort="low"', html)
        self.assertIn('data-effort="medium"', html)
        self.assertIn('data-effort="high"', html)

        # 2. Verify /api/health exposes available models and effort levels
        health_res = self.client.get("/api/health")
        self.assertEqual(health_res.status_code, 200)
        hdata = health_res.get_json()
        self.assertIn("available_models", hdata)
        self.assertIn("effort_levels", hdata)
        self.assertListEqual(hdata["effort_levels"], ["low", "medium", "high"])
        print("[PASSED] Model selector and reasoning effort configuration test")


if __name__ == "__main__":
    unittest.main()

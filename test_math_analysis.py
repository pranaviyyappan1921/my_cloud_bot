"""
Unit & Integration Test Suite for Advanced Mathematical Analysis & Reasoning Capability.
Tests:
1. Mathematical content & formula pattern detection
2. Specific domain concept mappings (Speedup S=Ts/Tp, y=mx+c, D=b^2-4ac, Matrices, Gradients, Bayes)
3. Prompt scaffolding with 7-step mathematical reasoning standard
4. Fallback structured mathematical analysis report generation
5. AI Assistant System Instruction integration
6. API chat endpoint handling for mathematical queries
7. Frontend KaTeX CDN and auto-render template inclusion
"""

import os
import json
import unittest
from dotenv import load_dotenv

load_dotenv()
os.environ["FLASK_SECRET_KEY"] = "test-math-secret-key"

from app import app
from utils.gemini_client import SYSTEM_INSTRUCTION, GeminiClient
from utils.math_analyzer import (
    detect_math_content,
    build_math_reasoning_prompt_enhancement,
    generate_fallback_math_report,
    CONCEPT_REGISTRY,
)


class MathAnalysisTestCase(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_01_detect_parallel_speedup_formula(self):
        """Verify automatic recognition of parallel computing speedup S = Ts / Tp."""
        query = "Calculate speedup S = Ts / Tp for Ts = 120s and Tp = 15s."
        res = detect_math_content(query)
        self.assertTrue(res["is_math"])
        matched_ids = [c["id"] for c in res["matched_concepts"]]
        self.assertIn("parallel_speedup", matched_ids)

        concept = next(c for c in res["matched_concepts"] if c["id"] == "parallel_speedup")
        self.assertIn("High Performance Computing (HPC)", concept["domains"])
        self.assertIn("Cloud Computing", concept["domains"])
        self.assertIn("T_s", concept["variables"])
        self.assertIn("T_p", concept["variables"])

    def test_02_detect_linear_equation(self):
        """Verify recognition of linear equation y = mx + c."""
        query = "Explain the equation y = mx + c and its application in linear regression."
        res = detect_math_content(query)
        self.assertTrue(res["is_math"])
        matched_ids = [c["id"] for c in res["matched_concepts"]]
        self.assertIn("linear_equation", matched_ids)

        concept = next(c for c in res["matched_concepts"] if c["id"] == "linear_equation")
        self.assertIn("AI / Machine Learning", concept["domains"])
        self.assertIn("Data Science", concept["domains"])

    def test_03_detect_quadratic_discriminant(self):
        """Verify recognition of quadratic discriminant D = b^2 - 4ac."""
        query = "What is the discriminant D = b^2 - 4ac and how does it determine root types?"
        res = detect_math_content(query)
        self.assertTrue(res["is_math"])
        matched_ids = [c["id"] for c in res["matched_concepts"]]
        self.assertIn("quadratic_discriminant", matched_ids)

        concept = next(c for c in res["matched_concepts"] if c["id"] == "quadratic_discriminant")
        self.assertIn("Computer Graphics (Ray Tracing)", concept["domains"])
        self.assertIn("Control Systems", concept["domains"])

    def test_04_detect_matrices_and_linear_algebra(self):
        """Verify recognition of matrix operations, transformations, and eigenvalues."""
        query = "How do transformation matrices and eigenvalues work in neural networks and robotics?"
        res = detect_math_content(query)
        self.assertTrue(res["is_math"])
        matched_ids = [c["id"] for c in res["matched_concepts"]]
        self.assertIn("matrix_algebra", matched_ids)

        concept = next(c for c in res["matched_concepts"] if c["id"] == "matrix_algebra")
        self.assertIn("AI / Deep Learning", concept["domains"])
        self.assertIn("Robotics", concept["domains"])
        self.assertIn("Computer Vision", concept["domains"])

    def test_05_detect_derivatives_and_gradients(self):
        """Verify recognition of derivatives, gradients, and optimization."""
        query = "Explain how gradients and partial derivatives are computed during backpropagation."
        res = detect_math_content(query)
        self.assertTrue(res["is_math"])
        matched_ids = [c["id"] for c in res["matched_concepts"]]
        self.assertIn("derivatives_gradients", matched_ids)

    def test_06_build_prompt_enhancement(self):
        """Verify the 7-step mathematical reasoning prompt directive structure."""
        math_info = detect_math_content("Analyze S = Ts / Tp for parallel scaling")
        prompt_directive = build_math_reasoning_prompt_enhancement(math_info)
        
        self.assertIn("Concept Identification", prompt_directive)
        self.assertIn("Mathematical Formulation", prompt_directive)
        self.assertIn("Variable & Symbol Breakdown", prompt_directive)
        self.assertIn("Step-by-Step Derivation", prompt_directive)
        self.assertIn("Result Verification & Sanity Check", prompt_directive)
        self.assertIn("Real-World Applications", prompt_directive)
        self.assertIn("Graph / Visualization", prompt_directive)
        self.assertIn("Parallel Computing Speedup", prompt_directive)

    def test_07_fallback_math_report(self):
        """Verify fallback structured mathematical analysis generation."""
        report = generate_fallback_math_report("S = Ts / Tp")
        self.assertIn("Parallel Computing Speedup", report)
        self.assertIn("T_s", report)
        self.assertIn("T_p", report)
        self.assertIn("High Performance Computing (HPC)", report)
        self.assertIn("Cloud Computing", report)
        self.assertIn("Verification & Sanity Check", report)

    def test_08_system_instruction_math_integration(self):
        """Verify SYSTEM_INSTRUCTION contains the Advanced Mathematical Analysis standards."""
        self.assertIn("Advanced Mathematical Reasoning", SYSTEM_INSTRUCTION)
        self.assertIn("S = Ts / Tp", SYSTEM_INSTRUCTION)
        self.assertIn("y = mx + c", SYSTEM_INSTRUCTION)
        self.assertIn("D = b^2 - 4ac", SYSTEM_INSTRUCTION)
        self.assertIn("High Performance Computing", SYSTEM_INSTRUCTION)
        self.assertIn("Computer Vision", SYSTEM_INSTRUCTION)
        self.assertIn("Robotics", SYSTEM_INSTRUCTION)
        self.assertIn("Control Systems", SYSTEM_INSTRUCTION)

    def test_09_html_katex_integration(self):
        """Verify index.html contains KaTeX CDN stylesheets and scripts."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn("katex.min.css", html)
        self.assertIn("katex.min.js", html)
        self.assertIn("auto-render.min.js", html)
        self.assertIn("Mathematical Analysis", html)


if __name__ == "__main__":
    unittest.main()

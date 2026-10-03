import os
import tempfile
import unittest
from pathlib import Path

_temporary_database = tempfile.TemporaryDirectory()
os.environ["DATABASE_PATH"] = str(Path(_temporary_database.name) / "api.db")

from fastapi.testclient import TestClient

from backend.main import app
from backend.config import settings


CSV = b"date,order_id,product,revenue,cost\n2026-10-01,O001,Bag A,100,60\n2026-10-02,O002,Bag B,200,80\n"


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client_context = TestClient(app)
        cls.client = cls.client_context.__enter__()
        username = "api_test_user"
        password = "strong-password"
        response = cls.client.post("/auth/register", json={"username": username, "password": password})
        if response.status_code not in (201, 400):
            raise AssertionError(response.text)
        login = cls.client.post("/auth/login", json={"username": username, "password": password})
        cls.headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    @classmethod
    def tearDownClass(cls):
        cls.client_context.__exit__(None, None, None)
        _temporary_database.cleanup()

    def test_health_and_auth_guard(self):
        self.assertEqual(self.client.get("/health").json()["status"], "ok")
        self.assertEqual(self.client.post("/dashboard/kpis", json={"rows": []}).status_code, 401)
        self.assertEqual(self.client.get("/auth/me", headers=self.headers).json()["role"], "user")
        oversized = self.client.get("/health", headers={"Content-Length": str(settings.max_upload_bytes + 1)})
        self.assertEqual(oversized.status_code, 413)

    def test_analyze_chat_and_report(self):
        analysis = self.client.post(
            "/datasets/analyze?filename=sales.csv",
            content=CSV,
            headers={**self.headers, "Content-Type": "text/csv"},
        )
        self.assertEqual(analysis.status_code, 200, analysis.text)
        self.assertEqual(analysis.json()["kpis"]["net_profit"], 160)

        rows = [
            {"date": "2026-10-01", "order_id": "O001", "product": "Bag A", "revenue": 100.0, "cost": 60.0},
            {"date": "2026-10-02", "order_id": "O002", "product": "Bag B", "revenue": 200.0, "cost": 80.0},
        ]
        self.assertEqual(
            self.client.post("/datasets/profile", json={"rows": rows}, headers=self.headers).json()["row_count"],
            2,
        )
        self.assertIn("score", self.client.post("/datasets/quality", json={"rows": rows}, headers=self.headers).json())
        self.assertIn("columns", self.client.post("/datasets/schema", json={"rows": rows}, headers=self.headers).json())
        chat = self.client.post("/chat/query", json={"rows": rows, "question": "Tóm tắt KPI"}, headers=self.headers)
        self.assertEqual(chat.status_code, 200, chat.text)
        self.assertIn("300.0", chat.json()["answer"])
        report = self.client.post("/reports/export?format=json", json={"rows": rows}, headers=self.headers)
        self.assertEqual(report.status_code, 200, report.text)
        pdf = self.client.post("/reports/export?format=pdf", json={"rows": rows}, headers=self.headers)
        self.assertEqual(pdf.status_code, 200, pdf.text)
        self.assertTrue(pdf.content.startswith(b"%PDF"))

    def test_user_cannot_generate_synthetic_data(self):
        response = self.client.post(
            "/synthetic/generate",
            json={"rows": [{"order_id": "1", "revenue": 1, "cost": 0}], "count": 1, "seed": 42},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()

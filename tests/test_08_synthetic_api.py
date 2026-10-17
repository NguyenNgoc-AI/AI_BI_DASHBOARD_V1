"""
Unit and integration tests for Synthetic Data Generator API Endpoints (Task 8 - Interactive Testing Layer).
Compatible with Python unittest and pytest using FastAPI TestClient.
"""

import unittest
from fastapi.testclient import TestClient
from backend.synthetic_generator.api.standalone_server import app


class TestSyntheticAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_api_health_and_root(self):
        """Verify API root status and endpoint catalog."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ONLINE")
        self.assertIn("endpoints", data)

    def test_02_get_scenarios(self):
        """Verify list of supported business simulation scenarios."""
        response = self.client.get("/api/v1/synthetic/scenarios")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("scenarios", data)
        scenario_ids = [s["id"] for s in data["scenarios"]]
        self.assertIn("baseline", scenario_ids)
        self.assertIn("holiday_peak", scenario_ids)
        self.assertIn("flash_sale", scenario_ids)

    def test_03_generate_synthetic_data_in_memory(self):
        """Verify POST /api/v1/synthetic/generate returns valid preview, KPIs and 100% pass rate."""
        payload = {
            "n_records": 100,
            "scenario": "baseline",
            "start_date": "2024-01-01",
            "end_date": "2024-06-30",
            "growth_rate": 0.0,
            "export_csv": False,
        }
        response = self.client.post("/api/v1/synthetic/generate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["status"], "SUCCESS")
        self.assertEqual(data["total_records"], 100)
        self.assertEqual(data["total_columns"], 38)
        self.assertEqual(data["pass_rate_pct"], 100.0)
        self.assertIn("summary_kpis", data)
        self.assertGreater(data["summary_kpis"]["total_gross_sales"], 0)
        self.assertEqual(len(data["preview_data"]), 20)

    def test_04_generate_scenario_with_growth(self):
        """Verify scenario with custom growth and discount parameters."""
        payload = {
            "n_records": 150,
            "scenario": "holiday_peak",
            "start_date": "2024-11-01",
            "end_date": "2024-12-31",
            "growth_rate": 0.25,
            "export_csv": False,
        }
        response = self.client.post("/api/v1/synthetic/generate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total_records"], 150)
        self.assertEqual(data["pass_rate_pct"], 100.0)

    def test_05_download_csv_stream(self):
        """Verify POST /api/v1/synthetic/download-csv streams a valid 38-column CSV file."""
        payload = {
            "n_records": 50,
            "scenario": "baseline",
            "start_date": "2024-01-01",
            "end_date": "2024-03-31",
            "growth_rate": 0.0,
        }
        response = self.client.post("/api/v1/synthetic/download-csv", json=payload)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("content-type"), "text/csv; charset=utf-8")
        
        csv_text = response.text
        lines = csv_text.strip().split("\n")
        header = lines[0].split(",")
        self.assertEqual(len(header), 38)
        self.assertEqual(len(lines), 51)  # 1 header + 50 data rows

    def test_06_compare_distribution(self):
        """Verify GET /api/v1/synthetic/compare-distribution returns statistical quantiles."""
        response = self.client.get("/api/v1/synthetic/compare-distribution?column=net_sales")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["column"], "net_sales")
        self.assertIn("real_distribution", data)
        self.assertIn("synthetic_distribution", data)
        self.assertIn("median", data["real_distribution"])
        self.assertIn("median", data["synthetic_distribution"])


if __name__ == "__main__":
    unittest.main()


"""
Unit and integration tests for Synthetic Data Generator API Endpoints (Task 8 - Interactive Testing Layer).
Compatible with Python unittest and pytest using FastAPI TestClient.
"""

import unittest
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

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

    def test_07_generate_export_csv_does_not_corrupt_gold_benchmark(self):
        """Verify that export_csv=True writes to exports/ directory and never overwrites the 50,000 gold benchmark."""
        from pathlib import Path
        gold_benchmark = Path("data/generated/synthetic_ecommerce.csv")
        self.assertTrue(gold_benchmark.exists())
        gold_mtime_before = gold_benchmark.stat().st_mtime

        payload = {
            "n_records": 30,
            "scenario": "baseline",
            "start_date": "2024-01-01",
            "end_date": "2024-03-31",
            "growth_rate": 0.0,
            "export_csv": True,
        }
        response = self.client.post("/api/v1/synthetic/generate", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        export_filepath = data.get("export_filepath")
        self.assertIsNotNone(export_filepath)
        self.assertIn("exports", export_filepath)

        exported_path = Path(export_filepath)
        self.assertTrue(exported_path.exists())

        # Clean up temporary exported file
        try:
            exported_path.unlink()
        except Exception:
            pass

        # Verify Gold Benchmark was untouched
        gold_mtime_after = gold_benchmark.stat().st_mtime
        self.assertEqual(gold_mtime_before, gold_mtime_after, "Gold benchmark was illegally modified during testing!")

    def test_08_date_logic_inversion_returns_422(self):
        """Fault Injection: Inverting dates (start_date > end_date) must be rejected with 422."""
        payload = {
            "n_records": 100,
            "scenario": "baseline",
            "start_date": "2025-12-31",
            "end_date": "2024-01-01",
        }
        response = self.client.post("/api/v1/synthetic/generate", json=payload)
        self.assertEqual(response.status_code, 422)
        data = response.json()
        error_str = str(data.get("detail", ""))
        self.assertIn("start_date cannot be after end_date", error_str)

    def test_09_invalid_column_compare_distribution_returns_400(self):
        """Fault Injection: Requesting comparison of non-existent column must be rejected with 400 Bad Request."""
        response = self.client.get("/api/v1/synthetic/compare-distribution?column=non_existent_column_xyz")
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("không tồn tại", data.get("detail", ""))

    def test_10_growth_rate_out_of_bounds_returns_422(self):
        """Fault Injection: Absurd growth rate (> 10.0 or < -1.0) must be rejected with 422."""
        payload = {
            "n_records": 50,
            "scenario": "baseline",
            "growth_rate": 50.0,
        }
        response = self.client.post("/api/v1/synthetic/generate", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_11_rbac_unauthorized_role_returns_403(self):
        """RBAC Security Test: Unauthorized role (Guest) must be blocked with 403 Forbidden."""
        payload = {
            "n_records": 50,
            "scenario": "baseline",
        }
        headers = {"X-User-Role": "guest"}
        response = self.client.post("/api/v1/synthetic/generate", json=payload, headers=headers)
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertIn("Truy cập bị từ chối", data.get("detail", ""))


if __name__ == "__main__":
    unittest.main()


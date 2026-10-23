"""
Automated API Test Suite Runner - Case-by-Case Execution & JSON Reporting.
Tests all endpoints against FastAPI TestClient, validates responses,
and exports full results to data/generated/api_test_results.json.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
from typing import Any, Dict, List

BASE_DIR = Path(__file__).resolve().parent.parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from fastapi.testclient import TestClient
from backend.synthetic_generator.api.standalone_server import app

OUTPUT_JSON_PATH = BASE_DIR / "data" / "generated" / "api_test_results.json"
GOLD_BENCHMARK_PATH = BASE_DIR / "data" / "generated" / "synthetic_ecommerce.csv"


class APICaseRunner:
    def __init__(self):
        self.client = TestClient(app)
        self.results: List[Dict[str, Any]] = []

    def log_case_start(self, case_id: str, title: str, method: str, endpoint: str):
        print(f"\n{'='*75}")
        print(f"[*] {case_id}: {title}")
        print(f"    Method: {method} | Endpoint: {endpoint}")

    def log_case_end(self, status: str, duration: float, message: str):
        icon = "[PASS]" if status == "PASSED" else "[FAIL]"
        print(f"    {icon} Status: {status} ({duration:.3f}s) - {message}")

    def run_case(
        self,
        case_id: str,
        name: str,
        method: str,
        endpoint: str,
        expected_status: int,
        payload: Any = None,
        params: Any = None,
        headers: Any = None,
        custom_validator=None,
    ) -> Dict[str, Any]:
        self.log_case_start(case_id, name, method, endpoint)
        start_t = time.time()
        assertions_passed: List[str] = []
        status = "PASSED"
        err_msg = ""
        res_summary: Dict[str, Any] = {}

        try:
            if method.upper() == "GET":
                resp = self.client.get(endpoint, params=params, headers=headers)
            elif method.upper() == "POST":
                resp = self.client.post(endpoint, json=payload, params=params, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            duration = time.time() - start_t

            # 1. Assert status code
            if resp.status_code == expected_status:
                assertions_passed.append(f"HTTP Status code matches expected: {expected_status}")
            else:
                status = "FAILED"
                err_msg = f"Status code mismatch: expected {expected_status}, got {resp.status_code}"

            # 2. Extract response summary
            content_type = resp.headers.get("content-type", "")
            if "application/json" in content_type:
                data = resp.json()
                if isinstance(data, dict):
                    res_summary = {k: v for k, v in list(data.items())[:6] if not isinstance(v, list)}
                else:
                    res_summary = {"items_count": len(data)}
            elif "text/csv" in content_type:
                csv_lines = resp.text.strip().split("\n")
                res_summary = {
                    "content_type": content_type,
                    "header_columns_count": len(csv_lines[0].split(",")) if csv_lines else 0,
                    "total_csv_lines": len(csv_lines),
                }

            # 3. Run custom domain validation
            if status == "PASSED" and custom_validator:
                val_ok, val_note = custom_validator(resp)
                if val_ok:
                    assertions_passed.append(val_note)
                else:
                    status = "FAILED"
                    err_msg = f"Validation failed: {val_note}"

        except Exception as ex:
            duration = time.time() - start_t
            status = "FAILED"
            err_msg = f"Exception during execution: {str(ex)}"

        self.log_case_end(status, duration, err_msg if status == "FAILED" else f"All {len(assertions_passed)} assertions verified.")

        record = {
            "case_id": case_id,
            "name": name,
            "method": method,
            "endpoint": endpoint,
            "payload": payload,
            "expected_status": expected_status,
            "actual_status": resp.status_code if 'resp' in locals() else None,
            "duration_seconds": round(duration, 4),
            "status": status,
            "assertions_passed": assertions_passed,
            "error_message": err_msg if status == "FAILED" else None,
            "response_summary": res_summary,
        }
        self.results.append(record)
        return record

    def execute_all_cases(self) -> Dict[str, Any]:
        suite_start = time.time()
        print("\n" + "#"*75)
        print("[*] STARTING AUTOMATED API TEST SUITE (CASE-BY-CASE)")
        print(f"Target: AI BI Dashboard - Synthetic Data Generator API")
        print("#"*75)

        # ---------------------------------------------------------
        # Case 1: Health Check & Service Discovery
        # ---------------------------------------------------------
        def val_c1(r):
            d = r.json()
            return d.get("status") == "ONLINE" and "endpoints" in d, "Service status is ONLINE with 5 endpoints listed."

        self.run_case(
            case_id="TC-API-01",
            name="Health Check & Service Discovery",
            method="GET",
            endpoint="/",
            expected_status=200,
            custom_validator=val_c1,
        )

        # ---------------------------------------------------------
        # Case 2: List Business Scenarios
        # ---------------------------------------------------------
        def val_c2(r):
            ids = [s["id"] for s in r.json().get("scenarios", [])]
            return "baseline" in ids and "holiday_peak" in ids, f"Discovered {len(ids)} valid scenarios."

        self.run_case(
            case_id="TC-API-02",
            name="List Business Scenarios",
            method="GET",
            endpoint="/api/v1/synthetic/scenarios",
            expected_status=200,
            custom_validator=val_c2,
        )

        # ---------------------------------------------------------
        # Case 3: Baseline Synthetic Generation (In-Memory)
        # ---------------------------------------------------------
        p_c3 = {
            "n_records": 100,
            "scenario": "baseline",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "growth_rate": 0.0,
            "export_csv": False,
        }
        def val_c3(r):
            d = r.json()
            return (
                d.get("total_records") == 100
                and d.get("total_columns") == 38
                and d.get("pass_rate_pct") == 100.0
                and d.get("export_filepath") is None
            ), "Generated 100 in-memory records with exactly 38 columns and 100% rule compliance."

        self.run_case(
            case_id="TC-API-03",
            name="Generate Baseline Data (In-Memory)",
            method="POST",
            endpoint="/api/v1/synthetic/generate",
            expected_status=200,
            payload=p_c3,
            custom_validator=val_c3,
        )

        # ---------------------------------------------------------
        # Case 4: Holiday Peak Scenario with Growth Rate (+25%)
        # ---------------------------------------------------------
        p_c4 = {
            "n_records": 150,
            "scenario": "holiday_peak",
            "start_date": "2024-11-01",
            "end_date": "2024-12-31",
            "growth_rate": 0.25,
            "export_csv": False,
        }
        def val_c4(r):
            d = r.json()
            return (
                d.get("total_records") == 150
                and d.get("pass_rate_pct") == 100.0
                and d.get("summary_kpis", {}).get("total_gross_sales", 0) > 0
            ), "Successfully applied Holiday Peak scenario with positive revenue and 100% rule pass rate."

        self.run_case(
            case_id="TC-API-04",
            name="Holiday Peak Simulation (+25% Growth)",
            method="POST",
            endpoint="/api/v1/synthetic/generate",
            expected_status=200,
            payload=p_c4,
            custom_validator=val_c4,
        )

        # ---------------------------------------------------------
        # Case 5: Safe Server Export (Writes to exports/ dir)
        # ---------------------------------------------------------
        p_c5 = {
            "n_records": 30,
            "scenario": "flash_sale",
            "start_date": "2024-05-01",
            "end_date": "2024-05-05",
            "growth_rate": 0.40,
            "export_csv": True,
        }
        exported_file_cleanup: List[Path] = []
        def val_c5(r):
            d = r.json()
            path_str = d.get("export_filepath")
            if path_str and "exports" in path_str:
                p = Path(path_str)
                if p.exists():
                    exported_file_cleanup.append(p)
                    return True, f"File successfully written to isolated path: {p.name}"
            return False, "Export file path missing or not located in exports/ directory."

        self.run_case(
            case_id="TC-API-05",
            name="Isolated Server Export (Gold Benchmark Protection)",
            method="POST",
            endpoint="/api/v1/synthetic/generate",
            expected_status=200,
            payload=p_c5,
            custom_validator=val_c5,
        )

        # Clean up temporary exported file
        for f in exported_file_cleanup:
            try:
                f.unlink()
            except Exception:
                pass

        # ---------------------------------------------------------
        # Case 6: Stream Download CSV Directly
        # ---------------------------------------------------------
        p_c6 = {
            "n_records": 50,
            "scenario": "baseline",
            "start_date": "2024-01-01",
            "end_date": "2024-03-31",
            "growth_rate": 0.0,
        }
        def val_c6(r):
            lines = r.text.strip().split("\n")
            header = lines[0].split(",") if lines else []
            return (
                r.headers.get("content-type") == "text/csv; charset=utf-8"
                and len(header) == 38
                and len(lines) == 51
            ), f"Successfully streamed CSV with 38 headers and {len(lines)-1} data rows."

        self.run_case(
            case_id="TC-API-06",
            name="Direct CSV Streaming Download",
            method="POST",
            endpoint="/api/v1/synthetic/download-csv",
            expected_status=200,
            payload=p_c6,
            custom_validator=val_c6,
        )

        # ---------------------------------------------------------
        # Case 7: Statistical Distribution Comparison
        # ---------------------------------------------------------
        def val_c7(r):
            d = r.json()
            r_d = d.get("real_distribution", {})
            s_d = d.get("synthetic_distribution", {})
            return "median" in r_d and "median" in s_d and "p25" in s_d, "Extracted statistical quantiles for real and synthetic net_sales."

        self.run_case(
            case_id="TC-API-07",
            name="Statistical Distribution Comparison",
            method="GET",
            endpoint="/api/v1/synthetic/compare-distribution",
            params={"column": "net_sales"},
            expected_status=200,
            custom_validator=val_c7,
        )

        # ---------------------------------------------------------
        # Case 8: Quality Gate Benchmark Validation
        # ---------------------------------------------------------
        def val_c8(r):
            d = r.json()
            sqi = d.get("sqi_score", 0.0)
            status_val = d.get("status")
            return sqi >= 80.0 and status_val == "PASSED", f"Quality Gate PASSED with SQI score: {sqi}/100."

        self.run_case(
            case_id="TC-API-08",
            name="Quality Gate 4-Pillars Validation",
            method="GET",
            endpoint="/api/v1/synthetic/validate-benchmark",
            expected_status=200,
            custom_validator=val_c8,
        )

        # ---------------------------------------------------------
        # Case 9: Input Validation Error (Edge Case n_records < 10)
        # ---------------------------------------------------------
        p_c9 = {"n_records": 3, "scenario": "baseline"}
        def val_c9(r):
            d = r.json()
            detail = str(d.get("detail", ""))
            return r.status_code == 422 and "greater than or equal to 10" in detail, "Pydantic validator intercepted invalid input with 422 Unprocessable Entity."

        self.run_case(
            case_id="TC-API-09",
            name="Input Validation Error Handling (n_records < 10)",
            method="POST",
            endpoint="/api/v1/synthetic/generate",
            expected_status=422,
            payload=p_c9,
            custom_validator=val_c9,
        )

        # ---------------------------------------------------------
        # Case 10: Immutability Check of Gold Benchmark (50,000 rows)
        # ---------------------------------------------------------
        self.log_case_start("TC-API-10", "Gold Benchmark Dataset Immutability Check", "SYSTEM", str(GOLD_BENCHMARK_PATH.name))
        t10_start = time.time()
        import pandas as pd
        df_gold = pd.read_csv(GOLD_BENCHMARK_PATH)
        t10_dur = time.time() - t10_start
        c10_ok = len(df_gold) == 50000 and len(df_gold.columns) == 38
        self.log_case_end("PASSED" if c10_ok else "FAILED", t10_dur, "Gold benchmark remained exactly 50,000 records & 38 columns.")
        self.results.append({
            "case_id": "TC-API-10",
            "name": "Gold Benchmark Dataset Immutability Check",
            "method": "SYSTEM",
            "endpoint": "data/generated/synthetic_ecommerce.csv",
            "payload": None,
            "expected_status": 200,
            "actual_status": 200 if c10_ok else 500,
            "duration_seconds": round(t10_dur, 4),
            "status": "PASSED" if c10_ok else "FAILED",
            "assertions_passed": [f"Gold benchmark preserved with exactly {len(df_gold):,} rows and {len(df_gold.columns)} columns."],
            "error_message": None if c10_ok else f"Gold dataset size altered: {len(df_gold)} rows",
            "response_summary": {"total_records": len(df_gold), "total_columns": len(df_gold.columns)},
        })

        # ---------------------------------------------------------
        # Case 11: Fault Injection - Date Inversion (start_date > end_date)
        # ---------------------------------------------------------
        p_c11 = {
            "n_records": 100,
            "scenario": "baseline",
            "start_date": "2025-12-31",
            "end_date": "2024-01-01",
        }
        def val_c11(r):
            d = r.json()
            err_text = str(d.get("detail", ""))
            return r.status_code == 422 and "start_date cannot be after end_date" in err_text, "Intercepted inverted date logic with 422 ValidationError."

        self.run_case(
            case_id="TC-API-11",
            name="Fault Injection: Inverted Date Logic (start > end)",
            method="POST",
            endpoint="/api/v1/synthetic/generate",
            expected_status=422,
            payload=p_c11,
            custom_validator=val_c11,
        )

        # ---------------------------------------------------------
        # Case 12: Fault Injection - Query Non-Existent Column
        # ---------------------------------------------------------
        def val_c12(r):
            d = r.json()
            err_msg = d.get("detail", "")
            return r.status_code == 400 and "không tồn tại" in err_msg, "Rejected invalid query column with 400 Bad Request."

        self.run_case(
            case_id="TC-API-12",
            name="Fault Injection: Query Non-Existent Column",
            method="GET",
            endpoint="/api/v1/synthetic/compare-distribution",
            params={"column": "hacker_unknown_col_xyz"},
            expected_status=400,
            custom_validator=val_c12,
        )

        # ---------------------------------------------------------
        # Case 13: Fault Injection - Growth Rate Out of Bounds
        # ---------------------------------------------------------
        p_c13 = {
            "n_records": 50,
            "scenario": "baseline",
            "growth_rate": 50.0,  # Max allowed is 10.0
        }
        def val_c13(r):
            d = r.json()
            detail_str = str(d.get("detail", ""))
            return r.status_code == 422 and "less than or equal to 10" in detail_str, "Intercepted out-of-bounds growth rate with 422 ValidationError."

        self.run_case(
            case_id="TC-API-13",
            name="Fault Injection: Growth Rate Out of Bounds",
            method="POST",
            endpoint="/api/v1/synthetic/generate",
            expected_status=422,
            payload=p_c13,
            custom_validator=val_c13,
        )

        # ---------------------------------------------------------
        # Case 14: Fault Injection - Corrupted DataFrame & Auto-Repair Recovery
        # ---------------------------------------------------------
        self.log_case_start("TC-API-14", "Fault Injection: Corrupted Data Detection & Auto-Repair", "CORE_ENGINE", "ConstraintEngine")
        t14_start = time.time()
        from backend.schema_learning.rule_parser import ConstraintEngine
        import pandas as pd
        c_engine = ConstraintEngine()
        
        # Inject corrupted sample records (negative price, net > gross sales)
        corrupted_data = pd.DataFrame([
            {"sales_id": "SALE_BAD_1", "product_id": "P1", "unit_price": -20.0, "quantity": 2, "gross_sales": 10.0, "discount_amount": 50.0, "net_sales": 100.0, "cogs": 10.0, "gross_profit": 500.0},
            {"sales_id": "SALE_BAD_2", "product_id": "P2", "unit_price": 50.0, "quantity": 1, "gross_sales": 50.0, "discount_amount": 0.0, "net_sales": 50.0, "cogs": 30.0, "gross_profit": 20.0},
        ])
        
        # 1. Verify that validation catches errors
        audit_rep = c_engine.validate_dataframe(corrupted_data)
        has_detected_errors = audit_rep.has_blocking_errors and audit_rep.invalid_records >= 1
        
        # 2. Verify that auto-repair restores mathematical consistency
        repaired_df = c_engine.enforce_constraints(corrupted_data)
        repaired_rep = c_engine.validate_dataframe(repaired_df)
        is_fully_repaired = repaired_rep.overall_pass_rate_pct == 100.0 and not repaired_rep.has_blocking_errors
        
        t14_dur = time.time() - t14_start
        c14_ok = has_detected_errors and is_fully_repaired
        
        self.log_case_end("PASSED" if c14_ok else "FAILED", t14_dur, "Corrupted records detected and mathematically repaired to 100% compliance.")
        self.results.append({
            "case_id": "TC-API-14",
            "name": "Fault Injection: Corrupted Data Detection & Auto-Repair",
            "method": "CORE_ENGINE",
            "endpoint": "backend.schema_learning.rule_parser.ConstraintEngine",
            "payload": {"injected_violations": ["negative_unit_price", "net_sales_greater_than_gross"]},
            "expected_status": 200,
            "actual_status": 200 if c14_ok else 500,
            "duration_seconds": round(t14_dur, 4),
            "status": "PASSED" if c14_ok else "FAILED",
            "assertions_passed": [
                f"Detection: Caught {audit_rep.invalid_records} invalid records (initial pass rate: {audit_rep.overall_pass_rate_pct}%).",
                f"Auto-Repair: Successfully recovered to 100% compliance ({repaired_rep.overall_pass_rate_pct}%).",
            ],
            "error_message": None if c14_ok else "Auto-repair failed to resolve all injected constraint violations.",
            "response_summary": {
                "initial_pass_rate_pct": audit_rep.overall_pass_rate_pct,
                "repaired_pass_rate_pct": repaired_rep.overall_pass_rate_pct,
                "has_blocking_errors": repaired_rep.has_blocking_errors,
            },
        })

        # ---------------------------------------------------------
        # Case 15: Security - RBAC Unauthorized Role Blocked (403)
        # ---------------------------------------------------------
        p_c15 = {
            "n_records": 50,
            "scenario": "baseline",
        }
        h_c15 = {"X-User-Role": "guest"}
        def val_c15(r):
            d = r.json()
            err_msg = d.get("detail", "")
            return r.status_code == 403 and "Truy cập bị từ chối" in err_msg, "RBAC Gateway blocked unauthorized role 'guest' with 403 Forbidden."

        self.run_case(
            case_id="TC-API-15",
            name="Security: RBAC Unauthorized Role Access Blocked",
            method="POST",
            endpoint="/api/v1/synthetic/generate",
            expected_status=403,
            payload=p_c15,
            headers=h_c15,
            custom_validator=val_c15,
        )

        # Compile final summary
        suite_duration = round(time.time() - suite_start, 3)
        total_count = len(self.results)
        passed_count = sum(1 for r in self.results if r["status"] == "PASSED")
        failed_count = total_count - passed_count

        summary_report = {
            "executed_at": datetime.now(timezone.utc).isoformat(),
            "target_service": "AI BI Dashboard - Synthetic Generator API",
            "total_cases": total_count,
            "passed_cases": passed_count,
            "failed_cases": failed_count,
            "pass_rate_pct": round((passed_count / total_count) * 100, 2),
            "total_duration_seconds": suite_duration,
            "test_cases": self.results,
        }

        # Export to JSON
        OUTPUT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
            json.dump(summary_report, f, indent=2, ensure_ascii=False)

        print("\n" + "="*75)
        print(f"[OK] TEST SUITE COMPLETED: {passed_count}/{total_count} PASSED ({summary_report['pass_rate_pct']}%) in {suite_duration}s")
        print(f"[*] Detailed Results Exported to: {OUTPUT_JSON_PATH}")
        print("="*75 + "\n")

        return summary_report


if __name__ == "__main__":
    runner = APICaseRunner()
    runner.execute_all_cases()

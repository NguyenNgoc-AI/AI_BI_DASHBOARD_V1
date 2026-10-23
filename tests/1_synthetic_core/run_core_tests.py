"""
Script runner for Group 1: Data Synthetic Core Test Suite (Tasks 1 - 7).
Executes all 7 core unit test suites sequentially and outputs a summary scorecard.
"""

from pathlib import Path
import sys
import time
import unittest

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

TEST_FILES = [
    ("Task 1: Schema Definition", "test_01_schema_definition.py"),
    ("Task 2: Business Rules & Auto-Repair", "test_02_business_rules.py"),
    ("Task 4: Profiling & Quality Audit", "test_03_profiling_and_quality.py"),
    ("Task 5: Schema Learning & Extractor", "test_04_schema_learning.py"),
    ("Task 6: Synthetic Generator Engine", "test_05_synthetic_generator.py"),
    ("Task 7: 4-Pillar Quality Gate", "test_06_quality_gate.py"),
    ("Task 3: Benchmark Datasets & Holdout", "test_07_benchmark_data.py"),
]


def run_all_core_tests():
    core_dir = Path(__file__).resolve().parent
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    print("=" * 80)
    print("AI BI DASHBOARD - DATA SYNTHETIC CORE TEST SUITE (NHÓM 1)")
    print("=" * 80)

    results = []
    total_start = time.time()

    for task_name, filename in TEST_FILES:
        file_path = core_dir / filename
        if not file_path.exists():
            print(f"[-] Missing test file: {filename}")
            continue

        module_name = f"tests.1_synthetic_core.{filename[:-3]}"
        module_start = time.time()
        sub_suite = loader.loadTestsFromName(module_name)
        runner = unittest.TextTestRunner(verbosity=0)
        res = runner.run(sub_suite)
        duration = time.time() - module_start

        passed = res.testsRun - len(res.failures) - len(res.errors)
        status = "PASSED" if (len(res.failures) == 0 and len(res.errors) == 0) else "FAILED"
        icon = "[PASS]" if status == "PASSED" else "[FAIL]"

        print(f" {icon} {task_name:<42} | Tests: {passed:>2}/{res.testsRun:<2} | {duration:.3f}s")
        results.append({
            "task": task_name,
            "file": filename,
            "total": res.testsRun,
            "passed": passed,
            "failed": len(res.failures) + len(res.errors),
            "status": status,
            "duration": duration,
        })

    total_duration = time.time() - total_start
    total_tests = sum(r["total"] for r in results)
    total_passed = sum(r["passed"] for r in results)
    total_failed = sum(r["failed"] for r in results)

    print("-" * 80)
    print(f"SUMMARY GROUP 1: {total_passed}/{total_tests} Tests PASSED | {total_duration:.3f}s")
    if total_failed == 0:
        print("[SUCCESS] All 7 core test suites in Group 1 PASSED (100% Valid)!")
    else:
        print(f"[WARNING] {total_failed} tests failed. Please review the detailed logs above.")
    print("=" * 80)

    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(run_all_core_tests())


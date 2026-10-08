import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


_temporary_database = tempfile.TemporaryDirectory()
os.environ["DATABASE_PATH"] = str(Path(_temporary_database.name) / "api.db")
os.environ["ADMIN_USERNAME"] = "api_admin"
os.environ["ADMIN_PASSWORD"] = "Admin-password-2026"

from fastapi.testclient import TestClient

from backend.auth import create_user, update_user_role
from backend.config import settings
from backend.main import app


CSV = b"date,order_id,product,revenue,cost\n2026-10-01,O001,Bag A,100,60\n2026-10-02,O002,Bag B,200,80\n"
ROWS = [
    {"date": "2026-10-01", "order_id": "O001", "product": "Bag A", "revenue": 100.0, "cost": 60.0},
    {"date": "2026-10-02", "order_id": "O002", "product": "Bag B", "revenue": 200.0, "cost": 80.0},
]


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client_context = TestClient(app)
        cls.client = cls.client_context.__enter__()
        cls.user = cls._register_and_login("api_user", "User-password-2026")
        manager = cls._register_and_login("api_manager", "Manager-password-2026")
        update_user_role(manager["id"], "manager", settings.database_path)
        cls.manager = cls._login("api_manager", "Manager-password-2026", manager["id"])
        cls.admin = cls._login("api_admin", "Admin-password-2026")
        cls.target = cls._register_and_login("role_target", "Target-password-2026")

    @classmethod
    def tearDownClass(cls):
        cls.client_context.__exit__(None, None, None)
        _temporary_database.cleanup()

    @classmethod
    def _register_and_login(cls, username, password):
        created = create_user(username, password, settings.database_path)
        return cls._login(username, password, created["id"])

    @classmethod
    def _login(cls, username, password, user_id=None):
        response = cls.client.post("/auth/login", json={"username": username, "password": password})
        if response.status_code != 200:
            raise AssertionError(response.text)
        return {"id": user_id, "headers": {"Authorization": f"Bearer {response.json()['access_token']}"}}

    def test_public_auth_guards_cors_and_openapi(self):
        self.assertEqual(self.client.get("/").json()["docs"], "/docs")
        self.assertEqual(self.client.get("/health").json(), {"status": "ok", "version": "0.1.0"})
        self.assertEqual(self.client.post("/dashboard/kpis", json={"rows": ROWS}).status_code, 401)
        self.assertEqual(self.client.get("/auth/me", headers={"Authorization": "Basic bad"}).status_code, 401)
        self.assertEqual(self.client.get("/auth/me", headers=self.user["headers"]).json()["role"], "user")
        oversized = self.client.get("/health", headers={"Content-Length": str(settings.max_upload_bytes + 1)})
        self.assertEqual(oversized.status_code, 413)

        allowed = self.client.options(
            "/dashboard/kpis",
            headers={"Origin": settings.cors_origins[0], "Access-Control-Request-Method": "POST"},
        )
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.headers["access-control-allow-origin"], settings.cors_origins[0])
        denied = self.client.options(
            "/dashboard/kpis",
            headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
        )
        self.assertNotIn("access-control-allow-origin", denied.headers)

        schema = self.client.get("/openapi.json").json()
        self.assertIn("HTTPBearer", schema["components"]["securitySchemes"])
        self.assertIn("AnalysisResponse", schema["components"]["schemas"])
        self.assertTrue(schema["paths"]["/auth/me"]["get"]["security"])
        self.assertIn("requestBody", schema["paths"]["/datasets/analyze"]["post"])
        analysis_schema = schema["paths"]["/datasets/analyze"]["post"]["responses"]["200"]["content"]["application/json"]["schema"]
        self.assertEqual(analysis_schema["$ref"], "#/components/schemas/AnalysisResponse")
        self.assertIn("401", schema["paths"]["/dashboard/kpis"]["post"]["responses"])
        self.assertIn("403", schema["paths"]["/synthetic/generate"]["post"]["responses"])

    def test_user_can_use_every_private_analytics_endpoint(self):
        analysis = self.client.post(
            "/datasets/analyze?filename=sales.csv",
            content=CSV,
            headers={**self.user["headers"], "Content-Type": "application/octet-stream"},
        )
        self.assertEqual(analysis.status_code, 200, analysis.text)
        self.assertEqual(analysis.json()["kpis"]["net_profit"], 160)

        profile = self.client.post("/datasets/profile", json={"rows": ROWS}, headers=self.user["headers"])
        quality = self.client.post("/datasets/quality", json={"rows": ROWS}, headers=self.user["headers"])
        schema = self.client.post("/datasets/schema", json={"rows": ROWS}, headers=self.user["headers"])
        kpis = self.client.post("/dashboard/kpis", json={"rows": ROWS}, headers=self.user["headers"])
        charts = self.client.post("/dashboard/charts", json={"rows": ROWS}, headers=self.user["headers"])
        self.assertEqual(profile.json()["row_count"], 2)
        self.assertEqual(quality.json()["score"], 1.0)
        self.assertEqual(schema.json()["columns"]["revenue"]["type"], "float")
        self.assertEqual(kpis.json()["net_profit"], 160)
        self.assertTrue(charts.json())

        relations = self.client.post(
            "/schema/infer-relations",
            json={"tables": {
                "customers": [{"customer_id": "C1"}, {"customer_id": "C2"}],
                "orders": [{"order_id": "O1", "customer_id": "C1"}, {"order_id": "O2", "customer_id": "C2"}],
            }},
            headers=self.user["headers"],
        )
        self.assertEqual(relations.status_code, 200, relations.text)
        self.assertEqual(relations.json()["foreign_keys"][0]["child_table"], "orders")

        chat = self.client.post(
            "/chat/query", json={"rows": ROWS, "question": "Tóm tắt KPI"}, headers=self.user["headers"]
        )
        sql = self.client.post(
            "/chat/sql", json={"rows": ROWS, "question": "Doanh thu theo sản phẩm"}, headers=self.user["headers"]
        )
        self.assertEqual(chat.status_code, 200, chat.text)
        self.assertIn("300.0", chat.json()["answer"])
        self.assertEqual(sql.status_code, 200, sql.text)
        self.assertTrue(sql.json()["sql"].startswith("SELECT"))

        signatures = {"pdf": b"%PDF", "xlsx": b"PK", "pptx": b"PK"}
        for report_format in ("json", "csv", "html", "pdf", "xlsx", "pptx"):
            report = self.client.post(
                f"/reports/export?format={report_format}", json={"rows": ROWS}, headers=self.user["headers"]
            )
            self.assertEqual(report.status_code, 200, f"{report_format}: {report.text}")
            self.assertIn(f"report.{report_format}", report.headers["content-disposition"])
            if report_format in signatures:
                self.assertTrue(report.content.startswith(signatures[report_format]))

    def test_role_matrix_and_synthetic_workflow(self):
        payload = {"rows": ROWS, "count": 3, "seed": 42, "model": "bootstrap"}
        self.assertEqual(
            self.client.post("/synthetic/generate", json=payload, headers=self.user["headers"]).status_code, 403
        )
        generated = self.client.post("/synthetic/generate", json=payload, headers=self.manager["headers"])
        self.assertEqual(generated.status_code, 200, generated.text)
        self.assertEqual(len(generated.json()["rows"]), 3)
        validation = self.client.post(
            "/synthetic/validate",
            json={"original_rows": ROWS, "synthetic_rows": generated.json()["rows"]},
            headers=self.manager["headers"],
        )
        self.assertEqual(validation.status_code, 200, validation.text)
        self.assertEqual(set(validation.json()), {"validity", "fidelity", "privacy", "utility", "details"})

        role_path = f"/auth/users/{self.target['id']}/role"
        self.assertEqual(
            self.client.post(role_path, json={"role": "manager"}, headers=self.manager["headers"]).status_code, 403
        )
        changed = self.client.post(role_path, json={"role": "manager"}, headers=self.admin["headers"])
        self.assertEqual(changed.status_code, 200, changed.text)
        self.assertEqual(changed.json()["role"], "manager")

    def test_validation_and_sanitized_errors(self):
        invalid_cases = [
            self.client.post("/chat/query", json={"rows": ROWS, "question": ""}, headers=self.user["headers"]),
            self.client.post(
                "/synthetic/generate",
                json={"rows": ROWS, "count": 0, "model": "bootstrap"}, headers=self.manager["headers"]
            ),
            self.client.post(
                "/dashboard/kpis", json={"rows": ROWS, "unexpected": True}, headers=self.user["headers"]
            ),
            self.client.post(
                f"/auth/users/{self.target['id']}/role", json={"role": "owner"}, headers=self.admin["headers"]
            ),
        ]
        self.assertTrue(all(response.status_code == 422 for response in invalid_cases))
        bad_rows = [{"order_id": "O1", "revenue": "not-a-number", "cost": 1}]
        self.assertEqual(
            self.client.post("/dashboard/kpis", json={"rows": bad_rows}, headers=self.user["headers"]).status_code,
            400,
        )

        with patch("backend.main.calculate_kpis", side_effect=RuntimeError("secret C:\\internal\\path")):
            with TestClient(app, raise_server_exceptions=False) as safe_client:
                response = safe_client.post("/dashboard/kpis", json={"rows": ROWS}, headers=self.user["headers"])
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["error"]["code"], "INTERNAL_ERROR")
        self.assertNotIn("secret", response.text)
        self.assertNotIn("C:\\internal\\path", response.text)

    def test_registration_approval_provision_and_activation(self):
        request_body = {
            "employee_id": "emp-2026",
            "full_name": "Nguyen Van An",
            "position": "Data Analyst",
            "department": "Finance",
        }
        submitted = self.client.post("/auth/register-request", json=request_body)
        self.assertEqual(submitted.status_code, 201, submitted.text)
        request_id = submitted.json()["id"]
        self.assertEqual(submitted.json()["employee_id"], "EMP-2026")
        self.assertEqual(self.client.post("/auth/register-request", json=request_body).status_code, 400)

        self.assertEqual(
            self.client.get("/admin/registration-requests", headers=self.user["headers"]).status_code, 403
        )
        pending = self.client.get(
            "/admin/registration-requests?status=PENDING", headers=self.admin["headers"]
        )
        self.assertTrue(any(item["id"] == request_id for item in pending.json()))

        approved = self.client.post(
            f"/admin/registration-requests/{request_id}/approve", json={}, headers=self.admin["headers"]
        )
        self.assertEqual(approved.status_code, 200, approved.text)
        self.assertEqual(approved.json()["status"], "APPROVED")
        repeated = self.client.post(
            f"/admin/registration-requests/{request_id}/approve", json={}, headers=self.admin["headers"]
        )
        self.assertEqual(repeated.status_code, 409)

        provision_body = {
            "registration_request_id": request_id,
            "temporary_password": "Temporary-password-2026",
            "role": "user",
            "permissions": ["dashboard:view", "dataset:view", "kpi:view"],
            "data_scope": "own",
        }
        provisioned = self.client.post(
            "/admin/users/provision", json=provision_body, headers=self.admin["headers"]
        )
        self.assertEqual(provisioned.status_code, 201, provisioned.text)
        self.assertEqual(provisioned.json()["status"], "PENDING_ACTIVATION")
        self.assertEqual(
            self.client.post("/admin/users/provision", json=provision_body, headers=self.admin["headers"]).status_code,
            409,
        )

        pending_login = self.client.post(
            "/auth/login", json={"username": "EMP-2026", "password": "Temporary-password-2026"}
        )
        self.assertEqual(pending_login.status_code, 200, pending_login.text)
        self.assertEqual(pending_login.json()["purpose"], "activation")
        activation_headers = {"Authorization": f"Bearer {pending_login.json()['access_token']}"}
        self.assertEqual(self.client.get("/auth/me", headers=activation_headers).status_code, 401)
        self.assertEqual(
            self.client.post(
                "/auth/activate",
                json={"new_password": "New-password-2026", "confirm_password": "wrong-password"},
                headers=activation_headers,
            ).status_code,
            400,
        )
        activated = self.client.post(
            "/auth/activate",
            json={"new_password": "New-password-2026", "confirm_password": "New-password-2026"},
            headers=activation_headers,
        )
        self.assertEqual(activated.status_code, 204, activated.text)
        self.assertEqual(
            self.client.post(
                "/auth/login", json={"username": "EMP-2026", "password": "Temporary-password-2026"}
            ).status_code,
            401,
        )
        active_login = self.client.post(
            "/auth/login", json={"username": "EMP-2026", "password": "New-password-2026"}
        )
        self.assertEqual(active_login.json()["purpose"], "access")
        active_headers = {"Authorization": f"Bearer {active_login.json()['access_token']}"}
        me = self.client.get("/auth/me", headers=active_headers)
        self.assertEqual(me.json()["status"], "ACTIVE")
        self.assertEqual(me.json()["data_scope"], "own")

    def test_registration_rejection_requires_reason(self):
        submitted = self.client.post("/auth/register", json={
            "employee_id": "EMP-REJECT", "full_name": "Rejected User",
            "position": "Intern", "department": "Finance",
        })
        request_id = submitted.json()["id"]
        missing_reason = self.client.post(
            f"/admin/registration-requests/{request_id}/reject", json={}, headers=self.admin["headers"]
        )
        self.assertEqual(missing_reason.status_code, 400)
        rejected = self.client.post(
            f"/admin/registration-requests/{request_id}/reject",
            json={"rejection_reason": "Employee record could not be verified"},
            headers=self.admin["headers"],
        )
        self.assertEqual(rejected.status_code, 200, rejected.text)
        self.assertEqual(rejected.json()["status"], "REJECTED")
        self.assertEqual(
            self.client.post("/auth/register", json={"username": "old", "password": "Old-password-2026"}).status_code,
            422,
        )


if __name__ == "__main__":
    unittest.main()

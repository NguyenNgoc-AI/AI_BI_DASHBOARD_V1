// Run against an isolated test server only. Credentials come from the environment.
import assert from "node:assert/strict";
import { ApiClient } from "../api.mjs";
import { sampleRows, parseDataset } from "../core.mjs";
const api = new ApiClient(process.env.TEST_API_URL || "http://127.0.0.1:8001");
const password = process.env.TEST_ADMIN_PASSWORD;
assert.ok(password, "Set TEST_ADMIN_PASSWORD for the isolated server");
const login = await api.post("/auth/login", {
  username: "frontend_test_admin",
  password,
});
api.token = login.access_token;
assert.equal((await api.request("/auth/me")).role, "admin");
const csv =
  "date,order_id,product,revenue,cost\n2026-10-01,O1,Bag,100,60\n2026-10-02,O2,Pen,200,80";
const rows = parseDataset(csv, "sample.csv");
const analysis = await api.post("/datasets/analyze?filename=sample.csv", csv, {
  raw: true,
});
assert.equal(analysis.kpis.total_revenue, 300);
assert.equal((await api.post("/dashboard/kpis", { rows })).net_profit, 160);
for (const format of ["pdf", "xlsx", "pptx", "csv", "html", "json"]) {
  const blob = await api.post(
    "/reports/export?format=" + format,
    { rows },
    { blob: true },
  );
  assert.ok(blob.size > 0);
  const bytes = new Uint8Array(await blob.arrayBuffer());
  if (format === "pdf")
    assert.equal(new TextDecoder().decode(bytes.slice(0, 4)), "%PDF");
  if (["xlsx", "pptx"].includes(format))
    assert.equal(new TextDecoder().decode(bytes.slice(0, 2)), "PK");
}
assert.ok(
  (await api.post("/chat/query", { rows, question: "Tổng doanh thu?" })).answer,
);
assert.match(
  (await api.post("/chat/sql", { rows, question: "Tổng doanh thu?" })).sql,
  /SELECT/i,
);
const synth = await api.post("/synthetic/generate", {
  rows: sampleRows,
  count: 8,
  seed: 42,
  model: "bootstrap",
});
assert.equal(synth.rows.length, 8);
const suffix = Date.now().toString().slice(-9);
const employee_id = "FE" + suffix;
const request = await api.post(
  "/auth/register-request",
  {
    employee_id,
    full_name: "Frontend test",
    position: "Tester",
    department: "QA",
  },
  { token: "" },
);
assert.equal(request.status, "PENDING");
await api.post(`/admin/registration-requests/${request.id}/approve`, {});
await api.post("/admin/users/provision", {
  registration_request_id: request.id,
  temporary_password: password,
  role: "user",
  permissions: ["dashboard:view"],
  data_scope: "own",
});
const temporary = await api.post(
  "/auth/login",
  { username: employee_id, password },
  { token: "" },
);
assert.equal(temporary.purpose, "activation");
await assert.rejects(
  api.request("/auth/me", { token: temporary.access_token }),
  (e) => e.status === 401,
);
await api.post(
  "/auth/activate",
  { new_password: password + "-new", confirm_password: password + "-new" },
  { token: temporary.access_token },
);
const active = await api.post(
  "/auth/login",
  { username: employee_id, password: password + "-new" },
  { token: "" },
);
assert.equal(active.purpose, "access");
await assert.rejects(
  api.request("/admin/registration-requests", { token: active.access_token }),
  (e) => e.status === 403,
);
await assert.rejects(
  api.post(
    "/synthetic/generate",
    { rows, count: 2 },
    { token: active.access_token },
  ),
  (e) => e.status === 403,
);
console.log(
  "PASS: auth lifecycle, activation guard, user RBAC, CSV parsing/upload, KPI, 6 exports, chat, SQL, synthetic via Frontend ApiClient.",
);

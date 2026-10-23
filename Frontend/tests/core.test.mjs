import test from "node:test";
import assert from "node:assert/strict";
import {
  parseDataset,
  escapeHtml,
  filterRows,
  chartBuckets,
  canAdmin,
  canGenerate,
  errorMessage,
} from "../core.mjs";
import { ApiClient, ApiError } from "../api.mjs";
test("CSV quoted commas, newlines, escaped quotes and BOM", () => {
  const r = parseDataset(
    '\uFEFFOrder ID,Product\r\nA1,"Bag, blue"\r\nA2,"a ""quote""\nline"',
    "x.csv",
  );
  assert.deepEqual(r, [
    { order_id: "A1", product: "Bag, blue" },
    { order_id: "A2", product: 'a "quote"\nline' },
  ]);
});
test("JSON accepts array/envelope and rejects nested/empty/duplicate columns", () => {
  assert.deepEqual(parseDataset('{"data":[{"Revenue":2}]}', "x.json"), [
    { revenue: 2 },
  ]);
  for (const text of ["[]", '{"data":[{"a":{}}]}', '[{"A":1,"a":2}]'])
    assert.throws(() => parseDataset(text, "x.json"));
  assert.throws(() => parseDataset("a,b\n1", "x.csv"));
  assert.throws(() => parseDataset('a\n"open', "x.csv"));
});
test("untrusted content is escaped", () =>
  assert.equal(escapeHtml("<script>\"&'"), "&lt;script&gt;&quot;&amp;&#39;"));
test("filters preserve source and include boundaries", () => {
  const rows = [
    { date: "2026-10-01", product: "A" },
    { date: "2026-10-02", product: "B" },
  ];
  assert.deepEqual(filterRows(rows, { from: "2026-10-01", to: "2026-10-01" }), [
    rows[0],
  ]);
  assert.equal(rows.length, 2);
});
test("chart buckets bound DOM nodes and preserve revenue totals", () => {
  const values = Array(100000).fill(3);
  const result = chartBuckets(
    values.map((_, i) => String(i)),
    values,
  );
  assert.ok(result.values.length <= 60);
  assert.equal(
    result.values.reduce((a, b) => a + b, 0),
    300000,
  );
});
test("role boundaries and validation error formatting", () => {
  assert.equal(canAdmin({ role: "user" }), false);
  assert.equal(canGenerate({ role: "manager" }), true);
  assert.equal(canGenerate(null), false);
  assert.match(
    errorMessage({ detail: [{ loc: ["body", "username"], msg: "too short" }] }),
    /username: too short/,
  );
});
test("API JSON, raw upload, blob and status errors", async () => {
  const original = globalThis.fetch;
  const client = new ApiClient("http://localhost:8000");
  client.token = "test-token";
  try {
    globalThis.fetch = async (url, options) => {
      assert.equal(options.headers.Authorization, "Bearer test-token");
      assert.equal(options.body, '{"a":1}');
      return new Response('{"ok":true}');
    };
    assert.deepEqual(await client.post("/test", { a: 1 }), { ok: true });
    globalThis.fetch = async (url, options) => {
      assert.equal(options.headers["Content-Type"], "application/octet-stream");
      assert.equal(options.body, "a,b\n1,2");
      return new Response("PDF");
    };
    assert.equal(
      await (
        await client.post("/upload", "a,b\n1,2", { raw: true, blob: true })
      ).text(),
      "PDF",
    );
    globalThis.fetch = async () =>
      new Response('{"detail":"Forbidden"}', { status: 403 });
    await assert.rejects(
      client.request("/private"),
      (e) => e instanceof ApiError && e.status === 403,
    );
    globalThis.fetch = async () => new Response(null, { status: 204 });
    assert.equal(await client.request("/activate"), null);
  } finally {
    globalThis.fetch = original;
  }
});

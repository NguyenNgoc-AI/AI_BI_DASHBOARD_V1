// Pure helpers shared by the interface and the Node regression tests.
export const escapeHtml = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
export const money = (value) =>
  value == null
    ? "Chưa đủ dữ liệu"
    : new Intl.NumberFormat("vi-VN", {
        style: "currency",
        currency: "VND",
        maximumFractionDigits: 0,
      }).format(value);
export const number = (value) =>
  new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 2 }).format(
    value ?? 0,
  );
export function errorMessage(body) {
  const detail = body?.detail ?? body?.error?.message ?? body?.message;
  if (Array.isArray(detail))
    return detail
      .map((e) => `${(e.loc || []).slice(1).join(".")}: ${e.msg}`)
      .join("; ");
  return typeof detail === "string"
    ? detail
    : "Yêu cầu thất bại. Vui lòng thử lại.";
}
export function parseDataset(text, filename) {
  text = text.replace(/^\uFEFF/, "");
  let rows;
  if (/\.json$/i.test(filename)) {
    const parsed = JSON.parse(text);
    rows = Array.isArray(parsed) ? parsed : parsed.data;
  } else if (/\.csv$/i.test(filename)) {
    const records = [];
    let row = [],
      cell = "",
      quoted = false;
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (c === '"') {
        if (quoted && text[i + 1] === '"') {
          cell += '"';
          i++;
        } else quoted = !quoted;
      } else if (c === "," && !quoted) {
        row.push(cell);
        cell = "";
      } else if ((c === "\n" || c === "\r") && !quoted) {
        if (c === "\r" && text[i + 1] === "\n") i++;
        row.push(cell);
        if (row.some((v) => v !== "")) records.push(row);
        row = [];
        cell = "";
      } else cell += c;
    }
    if (quoted) throw new Error("CSV có dấu ngoặc kép chưa đóng.");
    row.push(cell);
    if (row.some((v) => v !== "")) records.push(row);
    const headers = records.shift();
    if (!headers?.length) throw new Error("Tệp CSV trống.");
    rows = records.map((r, i) => {
      if (r.length !== headers.length)
        throw new Error(`Dòng ${i + 2} có số cột không khớp.`);
      return Object.fromEntries(headers.map((h, j) => [h, r[j]]));
    });
  } else throw new Error("Chỉ hỗ trợ tệp CSV và JSON.");
  if (!Array.isArray(rows) || !rows.length || rows.length > 200000)
    throw new Error("Dữ liệu cần từ 1 đến 200.000 dòng.");
  return rows.map((row) => {
    if (!row || Array.isArray(row) || typeof row !== "object")
      throw new Error("Mỗi dòng phải là một object.");
    const normalized = {};
    for (const [key, value] of Object.entries(row)) {
      const name = key
        .trim()
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "_")
        .replace(/^_|_$/g, "");
      if (!name || Object.hasOwn(normalized, name))
        throw new Error("Tên cột trống hoặc trùng sau chuẩn hóa.");
      if (value !== null && typeof value === "object")
        throw new Error("Không hỗ trợ JSON lồng nhau.");
      normalized[name] = value;
    }
    return normalized;
  });
}
export function filterRows(rows, { from = "", to = "", product = "" } = {}) {
  return rows.filter(
    (r) =>
      (!from || r.date >= from) &&
      (!to || r.date <= to) &&
      (!product || r.product === product),
  );
}
export function chartBuckets(labels, values, limit = 60) {
  const size = Math.max(1, Math.ceil(values.length / limit));
  const result = { labels: [], values: [] };
  for (let i = 0; i < values.length; i += size) {
    result.labels.push(labels[i]);
    result.values.push(
      values.slice(i, i + size).reduce((sum, v) => sum + v, 0),
    );
  }
  return result;
}
export const canAdmin = (user) => user?.role === "admin";
export const canGenerate = (user) => ["admin", "manager"].includes(user?.role);
export const sampleRows = Array.from({ length: 24 }, (_, i) => ({
  date: `2026-${String(Math.floor(i / 2) + 1).padStart(2, "0")}-05`,
  order_id: `DEMO-${i + 1}`,
  product: ["Tai nghe Air", "Bàn phím cơ", "Chuột không dây"][i % 3],
  revenue: 850000 + i * 73000,
  cost: 450000 + i * 29000,
  customer_id: `KH-${i % 8}`,
  ad_spend: 50000,
  new_customers: i % 2,
}));

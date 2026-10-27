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

const CANONICAL_ROLES = new Set([
  "date",
  "order_id",
  "product",
  "revenue",
  "cost",
]);

const ROLE_ALIASES = {
  date: [
    "date",
    "order_purchase_timestamp",
    "order_date",
    "purchase_date",
    "report_date",
    "created_at",
    "ngay_ban",
    "ngay_dat_hang",
    "ngay_mua",
    "thoi_gian_mua",
    "ngay_ghi_nhan",
    "ngay_bao_cao",
    "ngay",
  ],
  order_id: [
    "order_id",
    "sales_id",
    "order_item_id",
    "invoice_no",
    "financial_record_id",
    "ma_don_hang",
    "ma_don",
    "so_don_hang",
    "id_don_hang",
    "ma_dong_ban",
  ],
  product: [
    "product",
    "product_name",
    "sub_category",
    "subcategory",
    "category",
    "product_id",
    "sku",
    "item_name",
    "title",
    "san_pham",
    "ten_san_pham",
    "ten_mat_hang",
    "ten_hang_hoa",
    "mat_hang",
    "danh_muc_con",
    "danh_muc",
    "nganh_hang",
    "nhom_san_pham",
    "ma_san_pham",
  ],
  revenue: [
    "revenue",
    "net_sales",
    "net_revenue",
    "gross_revenue",
    "gross_sales",
    "total_price",
    "payment_value",
    "doanh_thu",
    "doanh_so",
    "doanh_thu_thuan",
    "doanh_so_thuan",
    "tong_doanh_thu",
    "doanh_thu_gop",
    "tong_tien_hang",
    "thanh_tien",
  ],
  cost: [
    "cost",
    "cogs",
    "cogs_total",
    "total_cogs",
    "unit_cost",
    "gia_von",
    "chi_phi",
    "tong_gia_von",
    "gia_von_hang_ban",
    "don_gia_von",
    "gia_nhap",
    "chi_phi_san_xuat",
  ],
};

function normalizeToken(value) {
  return String(value ?? "")
    .trim()
    .toLowerCase()
    .replace(/đ/g, "d")
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_|_$/g, "");
}

function cleanHeader(rawKey) {
  const trimmed = String(rawKey ?? "").trim();
  if (!trimmed) return "";
  if (/^[\x00-\x7F]+$/.test(trimmed)) {
    const asciiSlug = trimmed
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/^_|_$/g, "");
    if (CANONICAL_ROLES.has(asciiSlug)) return asciiSlug;
  }
  return trimmed;
}

function resolveRoleHeaders(headers) {
  const tokenToHeader = new Map();
  for (const h of headers) {
    const token = normalizeToken(h);
    if (token && !tokenToHeader.has(token)) tokenToHeader.set(token, h);
  }
  const resolved = {};
  for (const [role, candidates] of Object.entries(ROLE_ALIASES)) {
    for (const candidate of candidates) {
      if (tokenToHeader.has(candidate)) {
        resolved[role] = tokenToHeader.get(candidate);
        break;
      }
    }
  }
  return resolved;
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
  if (!Array.isArray(rows) || !rows.length || rows.length > 100000)
    throw new Error("Dữ liệu cần từ 1 đến 100.000 dòng.");

  let roleMap = null;
  return rows.map((row) => {
    if (!row || Array.isArray(row) || typeof row !== "object")
      throw new Error("Mỗi dòng phải là một object.");
    const normalized = {};
    const seenTokens = new Set();
    for (const [key, value] of Object.entries(row)) {
      const name = cleanHeader(key);
      const token = normalizeToken(name);
      if (!name || !token || seenTokens.has(token) || Object.hasOwn(normalized, name))
        throw new Error("Tên cột trống hoặc trùng sau chuẩn hóa.");
      if (value !== null && typeof value === "object")
        throw new Error("Không hỗ trợ JSON lồng nhau.");
      seenTokens.add(token);
      normalized[name] = value;
    }
    if (!roleMap) roleMap = resolveRoleHeaders(Object.keys(normalized));
    for (const [role, srcHeader] of Object.entries(roleMap)) {
      if (srcHeader && !Object.hasOwn(normalized, role)) {
        const rawVal = normalized[srcHeader];
        const roleVal =
          role === "date" && typeof rawVal === "string"
            ? rawVal.trim().slice(0, 10)
            : rawVal;
        Object.defineProperty(normalized, role, {
          value: roleVal,
          enumerable: false,
          configurable: true,
          writable: true,
        });
      }
    }
    return normalized;
  });
}
export function filterRows(rows, { from = "", to = "", product = "" } = {}) {
  return rows.filter((r) => {
    const d = String(r.date ?? "").trim().slice(0, 10);
    return (
      (!from || d >= from) &&
      (!to || d <= to) &&
      (!product || r.product === product)
    );
  });
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

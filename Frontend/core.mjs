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
    "invoice_date",
    "invoicedate",
    "transaction_date",
    "order_date",
    "purchase_date",
    "report_date",
    "created_at",
    "ngay_ban",
    "ngay_dat_hang",
    "ngay_hoa_don",
    "ngay_mua",
    "thoi_gian_mua",
    "ngay_ghi_nhan",
    "ngay_bao_cao",
    "ngay",
  ],
  order_id: [
    "order_id",
    "invoice_no",
    "invoiceno",
    "invoice",
    "sales_id",
    "order_item_id",
    "financial_record_id",
    "ma_don_hang",
    "ma_don",
    "so_don_hang",
    "so_hoa_don",
    "id_don_hang",
    "ma_dong_ban",
  ],
  product: [
    "product",
    "product_name",
    "description",
    "product_description",
    "sub_category",
    "subcategory",
    "category",
    "product_id",
    "stock_code",
    "stockcode",
    "sku",
    "item_name",
    "title",
    "san_pham",
    "ten_san_pham",
    "ten_mat_hang",
    "ten_hang_hoa",
    "mat_hang",
    "mo_ta_san_pham",
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
    "unit_price",
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
    .replace(/([a-z0-9])([A-Z])/g, "$1_$2")
    .replace(/([A-Z]+)([A-Z][a-z])/g, "$1_$2")
    .toLowerCase()
    .replace(/đ/g, "d")
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_|_$/g, "");
}

function normalizeDateString(raw) {
  const s = String(raw ?? "").trim();
  if (!s) return "";
  if (s.length >= 10 && s[4] === "-" && s[7] === "-") return s.slice(0, 10);
  if (s.includes("/")) {
    const datePart = s.split(/\s+/)[0];
    const parts = datePart.split("/").map(Number);
    if (parts.length === 3 && !parts.some(Number.isNaN)) {
      let [p1, p2, p3] = parts;
      if (p1 >= 1000) {
        return `${p1}-${String(p2).padStart(2, "0")}-${String(p3).padStart(2, "0")}`;
      }
      if (p3 < 100) p3 += p3 < 70 ? 2000 : 1900;
      const [day, month] = p1 > 12 ? [p1, p2] : p2 > 12 ? [p2, p1] : [p1, p2];
      return `${p3}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    }
  }
  return s.slice(0, 10);
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
  for (const [token, header] of tokenToHeader.entries()) {
    const parts = token.split("_");
    if (
      !resolved.date &&
      parts.some((p) => ["date", "timestamp", "time", "ngay"].includes(p))
    ) {
      resolved.date = header;
    }
    if (
      !resolved.order_id &&
      parts.some((p) => ["invoice", "order", "bill"].includes(p)) &&
      parts.some((p) => ["id", "no", "number", "code", "ma"].includes(p))
    ) {
      resolved.order_id = header;
    }
    if (
      !resolved.product &&
      parts.some((p) =>
        ["description", "desc", "title", "product", "item", "sku", "stock"].includes(p),
      )
    ) {
      resolved.product = header;
    }
  }
  return resolved;
}

function findTextMergeIndex(headers) {
  const roles = resolveRoleHeaders(headers);
  if (roles.product && headers.includes(roles.product)) {
    return headers.indexOf(roles.product);
  }
  for (let i = 0; i < headers.length; i++) {
    const tok = normalizeToken(headers[i]);
    if (
      tok.includes("description") ||
      tok.includes("desc") ||
      tok.includes("product") ||
      tok.includes("name") ||
      tok.includes("title")
    ) {
      return i;
    }
  }
  return Math.min(2, headers.length - 1);
}

export function parseDataset(text, filename, { tolerant = false } = {}) {
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
        if (quoted) {
          const nxt = text[i + 1] ?? "";
          if (nxt === '"') {
            cell += '"';
            i++;
          } else if (nxt === "," || nxt === "\r" || nxt === "\n" || nxt === "") {
            quoted = false;
          } else {
            cell += '"';
          }
        } else if (cell === "") {
          quoted = true;
        } else {
          cell += '"';
        }
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
    if (headers.length > 1 && !String(headers[0]).trim()) {
      headers[0] = "row_index";
    }
    const mergeIdx = findTextMergeIndex(headers);
    const structuralErrors = [];
    rows = records.map((r, i) => {
      const originalLen = r.length;
      if (r.length > headers.length) {
        const extra = r.length - headers.length;
        const merged = r.slice(mergeIdx, mergeIdx + 1 + extra).join(", ");
        r = [
          ...r.slice(0, mergeIdx),
          merged,
          ...r.slice(mergeIdx + 1 + extra),
        ];
        if (r.length > headers.length) {
          if (!tolerant) throw new Error(`Dòng ${i + 2} có số cột không khớp.`);
          r = r.slice(0, headers.length);
          structuralErrors.push({
            row_index: i + 2,
            actual: originalLen,
            expected: headers.length,
            issue: "EXTRA_COLUMNS",
          });
        }
      } else if (r.length < headers.length) {
        if (!tolerant) throw new Error(`Dòng ${i + 2} có số cột không khớp.`);
        while (r.length < headers.length) r.push("");
        structuralErrors.push({
          row_index: i + 2,
          actual: originalLen,
          expected: headers.length,
          issue: "MISSING_COLUMNS",
        });
      }
      return Object.fromEntries(headers.map((h, j) => [h, r[j]]));
    });
    rows.structural_errors = structuralErrors;
  } else throw new Error("Chỉ hỗ trợ tệp CSV và JSON.");
  if (!Array.isArray(rows) || !rows.length || rows.length > 500000)
    throw new Error("Dữ liệu cần từ 1 đến 500.000 dòng.");

  let roleMap = null;
  const result = rows.map((row) => {
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
            ? normalizeDateString(rawVal)
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
  Object.defineProperty(result, "structural_errors", {
    value: rows.structural_errors || [],
    enumerable: false,
    configurable: true,
    writable: true,
  });
  return result;
}
export function filterRows(rows, { from = "", to = "", product = "" } = {}) {
  return rows.filter((r) => {
    const d = normalizeDateString(r.date);
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

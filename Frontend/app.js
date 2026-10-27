import { ApiClient } from "./api.mjs";
import {
  escapeHtml as esc,
  money,
  number,
  parseDataset,
  filterRows,
  chartBuckets,
  canAdmin,
  canGenerate,
  sampleRows,
} from "./core.mjs";

const api = new ApiClient(
  localStorage.getItem("candy.api") || "http://127.0.0.1:8000",
);
const root = document.querySelector("#app");
const state = {
  user: null,
  activation: "",
  auth: "login",
  page: "overview",
  rows: [],
  analysis: null,
  name: "",
  demo: false,
  messages: [],
  reports: [],
  requests: [],
  filter: {},
  busy: false,
  error: "",
  result: null,
};
const pages = [
  ["overview", "⌂", "Tổng quan"],
  ["reports", "▤", "Báo cáo"],
  ["chat", "✧", "Phân tích AI"],
  ["data", "▱", "Dữ liệu"],
  ["products", "◇", "Sản phẩm"],
  ["finance", "▥", "Tài chính"],
  ["synthetic", "⊞", "Dữ liệu tổng hợp"],
  ["admin", "♙", "Quản trị tài khoản"],
  ["settings", "⚙", "Cài đặt"],
];
const brand = () =>
  '<div class="brand"><span class="logo"><i></i><i></i><i></i></span><span>Code Candy<small>AI BI Dashboard</small></span></div>';
const robot = () => '<div class="robot" aria-hidden="true"></div>';
const button = (text, action, cls = "primary") =>
  `<button type="button" class="${cls}" data-action="${action}">${text}</button>`;
const field = (label, name, type = "text", extra = "") =>
  `<label>${label}<input name="${name}" type="${type}" ${extra} required></label>`;
const jsonBlock = (value) =>
  `<pre>${esc(JSON.stringify(value, null, 2))}</pre>`;
function toast(text) {
  document.querySelector("#notice").textContent = text;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(
    () => (document.querySelector("#notice").textContent = ""),
    6500,
  );
}
function saveFile(blob, name) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
function resetSession() {
  api.token = "";
  state.user = null;
  state.activation = "";
  state.auth = "login";
  state.rows = [];
  state.analysis = null;
  state.messages = [];
  state.reports = [];
  state.requests = [];
  state.result = null;
  state.filter = {};
  state.name = "";
  state.demo = false;
}
async function run(task) {
  if (state.busy) return;
  state.busy = true;
  state.error = "";
  const overlay = document.createElement("div");
  overlay.className = "loading-overlay";
  overlay.setAttribute("role", "status");
  overlay.innerHTML = '<div><div class="spinner"></div>Đang xử lý…</div>';
  document.body.append(overlay);
  try {
    await task();
  } catch (error) {
    if (error.status === 401 && state.user) {
      resetSession();
      state.error = "Phiên đăng nhập hết hạn. Vui lòng đăng nhập lại.";
    } else state.error = error.message;
  } finally {
    state.busy = false;
    overlay.remove();
    render();
  }
}
function authView() {
  if (state.auth === "connection")
    return `<main class="auth-page"><section class="card" style="width:min(480px,100%)">${brand()}<h1 class="section-gap">Cài đặt kết nối</h1><p>Địa chỉ API backend cho phiên làm việc.</p>${state.error ? `<div class="error" role="alert">${esc(state.error)}</div>` : ""}<form data-form="settings"><label>API Base URL<input name="base" type="url" required value="${esc(api.base)}"></label><button class="primary">Lưu kết nối</button></form><div class="section-gap">${button("← Trở lại đăng nhập", "login", "ghost")}</div></section></main>`;
  let title = "Đăng nhập",
    sub = "Chào mừng quay lại! Đăng nhập để khám phá dữ liệu.",
    fields = "",
    submit = "Đăng nhập →",
    form = "login";
  if (state.auth === "register") {
    title = "Yêu cầu tài khoản";
    sub = "Gửi thông tin để quản trị viên phê duyệt và cấp tài khoản.";
    form = "register";
    submit = "Gửi yêu cầu →";
    fields =
      field(
        "Mã nhân viên",
        "employee_id",
        "text",
        'minlength="3" maxlength="32" placeholder="VD: NV001"',
      ) +
      field(
        "Họ và tên",
        "full_name",
        "text",
        'maxlength="128" autocomplete="name"',
      ) +
      field("Chức vụ", "position", "text", 'maxlength="128"') +
      field("Phòng ban", "department", "text", 'maxlength="128"');
  } else if (state.auth === "activate") {
    title = "Kích hoạt tài khoản";
    sub = "Đổi mật khẩu tạm trước khi bắt đầu sử dụng hệ thống.";
    form = "activate";
    submit = "Kích hoạt tài khoản →";
    fields =
      field(
        "Mật khẩu mới",
        "new_password",
        "password",
        'minlength="8" maxlength="256" autocomplete="new-password"',
      ) +
      field(
        "Nhập lại mật khẩu",
        "confirm_password",
        "password",
        'minlength="8" maxlength="256" autocomplete="new-password"',
      );
  } else
    fields =
      field(
        "Tên đăng nhập / Mã nhân viên",
        "username",
        "text",
        'minlength="3" maxlength="64" autocomplete="username" placeholder="Nhập mã nhân viên của bạn"',
      ) +
      field(
        "Mật khẩu",
        "password",
        "password",
        'minlength="8" maxlength="256" autocomplete="current-password" placeholder="Nhập mật khẩu"',
      );
  const success = state.auth === "registered";
  return `<main class="auth-page"><section class="auth-card"><div class="auth-form">${brand()}${success ? `<div class="success-symbol">✓</div><h1>Đã gửi yêu cầu!</h1><p>Yêu cầu đang chờ quản trị viên phê duyệt. Bạn sẽ nhận tài khoản và mật khẩu tạm qua kênh nội bộ.</p>${button("Trở lại đăng nhập", "login")}` : `<div class="eyebrow">Không gian làm việc của bạn</div><h1>${title}</h1><p>${sub}</p>${state.error ? `<div class="error" role="alert">${esc(state.error)}</div>` : ""}<form data-form="${form}">${fields}${form === "login" ? '<div class="auth-links"><span>Bảo mật trong phiên làm việc</span><button type="button" data-action="forgot">Quên mật khẩu?</button></div>' : ""}<button class="primary" type="submit">${submit}</button></form><div class="auth-links">${button(state.auth === "login" ? "Chưa có tài khoản? Gửi yêu cầu" : "← Trở lại đăng nhập", state.auth === "login" ? "register" : "login", "ghost")}${button("Cài đặt kết nối", "connection", "ghost")}</div>`}</div><div class="auth-art">${robot()}<small>CHÀO MỪNG ĐẾN VỚI</small><h2>Code Candy</h2><p>Biến dữ liệu thành hiểu biết.<br>Biến hiểu biết thành hành động.</p><small>— AI BI DASHBOARD —</small><br><br><p>Một không gian. Mọi góc nhìn.</p>${button("Khám phá cùng dữ liệu của bạn", "login", "ghost")}</div></section></main>`;
}
function shell() {
  const visible = pages
    .filter(([key]) => key !== "admin" || canAdmin(state.user))
    .filter(([key]) => key !== "synthetic" || canGenerate(state.user));
  return `<div class="shell"><aside class="sidebar">${brand()}<nav class="nav" aria-label="Điều hướng chính">${visible.map(([key, icon, label]) => `<button data-page="${key}" class="${state.page === key ? "active" : ""}" ${state.page === key ? 'aria-current="page"' : ""}><span class="nav-icon">${icon}</span>${label}</button>`).join("")}</nav><div class="assistant-card">${robot()}<strong>AI Assistant</strong><p>Luôn sẵn sàng hỗ trợ<br>bạn khám phá dữ liệu!</p>${button("Chat với AI →", "chat")}</div></aside><header class="topbar"><button class="mobile-menu ghost" data-action="menu" aria-label="Mở menu">☰</button><form class="search" data-form="search"><input name="search" aria-label="Tìm trang" placeholder="⌕  Tìm báo cáo, dữ liệu, tính năng…"></form><div class="row"><span class="tag ${state.demo ? "orange" : "green"}">${state.demo ? "Dữ liệu mẫu" : "API trực tiếp"}</span><span class="avatar">${esc(state.user.username.slice(0, 1).toUpperCase())}</span><div class="user-info">${esc(state.user.username)}<small>${esc(state.user.role)} · ${esc(state.user.status)}</small></div><button class="ghost" data-action="logout" title="Đăng xuất" aria-label="Đăng xuất">↪</button></div></header><main class="content">${state.error ? `<div class="error" role="alert">${esc(state.error)}</div>` : ""}${pageView()}</main></div>`;
}
function heading(title, subtitle, action = "") {
  return `<div class="page-heading"><div><div class="eyebrow">Workspace / ${esc(title)}</div><h1>${title}</h1><p>${subtitle}</p></div>${action}</div>`;
}
function empty(
  title = "Chưa có dữ liệu để hiển thị",
  description = "Tải dữ liệu lên để bắt đầu phân tích và khám phá insight.",
) {
  return `<div class="empty"><div class="empty-symbol">♧</div><h2>${title}</h2><p>${description}</p>${button("＋ Tải dữ liệu ngay", "data")}</div>`;
}
function kpis() {
  const k = state.analysis?.kpis;
  return `<div class="kpis">${[
    [
      "Tổng doanh thu",
      k ? money(k.total_revenue) : "—",
      "↗ Doanh thu trong dữ liệu",
    ],
    ["Tổng đơn hàng", k ? number(k.order_count) : "—", "◇ Đơn hàng duy nhất"],
    ["Lợi nhuận", k ? money(k.net_profit) : "—", "Doanh thu − chi phí"],
    [
      "Giá trị trung bình / đơn",
      k ? money(k.average_order_value) : "—",
      "AOV từ dữ liệu hiện tại",
    ],
  ]
    .map(
      ([label, value, caption]) =>
        `<div class="kpi"><small>${label}</small><strong>${value}</strong><span class="tag">${caption}</span></div>`,
    )
    .join("")}</div>`;
}
function trend() {
  if (!state.analysis) return empty();
  const chart = state.analysis.charts.find((c) => c.type === "line");
  const { values, labels } = chartBuckets(
    chart?.x || [],
    chart?.series?.[0]?.data || [],
  );
  const max = Math.max(...values, 1);
  const n = values.length;
  const step = 640 / Math.max(n, 1);
  const points = values.map(
    (v, i) => `${50 + step * (i + 0.5)},${200 - (v / max) * 155}`,
  );
  const interval = (chart?.x?.length || 0) > 60 ? 'VND · gộp tối đa 60 khoảng, nhãn ngày đầu' : 'VND · theo ngày';
  return `<div class="legend"><span>Doanh thu</span><span>${interval}</span></div>
    <svg class="chart" viewBox="0 0 740 250" role="img" aria-label="Biểu đồ doanh thu theo thời gian">
      ${[0,1,2,3,4].map(i => `<line x1="50" y1="${200-i*40}" x2="710" y2="${200-i*40}" stroke="#eeeef7"/><text x="3" y="${204-i*40}">${number(max*i/4/1000000)}M</text>`).join('')}
      ${values.map((v,i) => `<rect x="${50+step*(i+.25)}" y="${200-v/max*155}" width="${Math.max(1,step*.5)}" height="${v/max*155}" rx="3" fill="#d2cef5"/>${i%Math.max(1,Math.ceil(n/8))===0 ? `<text x="${50+step*(i+.5)}" y="225" text-anchor="middle">${esc(labels[i])}</text>` : ''}`).join('')}
      <polyline points="${points.join(' ')}" fill="none" stroke="#7064dc" stroke-width="2.5"/>
      ${points.map(p => `<circle cx="${p.split(',')[0]}" cy="${p.split(',')[1]}" r="3" fill="#7064dc"/>`).join('')}
    </svg>`;
}
function products() {
  if (!state.analysis) return empty();
  const c = state.analysis.charts.find((c) => c.type === "bar");
  const vals = c?.series?.[0]?.data || [];
  const max = Math.max(...vals, 1);
  return `<div class="products">${(c?.x || [])
    .slice(0, 8)
    .map(
      (p, i) =>
        `<div class="product-row"><span class="product-dot">${i + 1}</span><div>${esc(p)}<div class="progress"><i style="width:${(vals[i] / max) * 100}%"></i></div></div><strong>${money(vals[i])}</strong></div>`,
    )
    .join("")}</div>`;
}
function overview() {
  return (
    heading(
      `Chào mừng trở lại, ${esc(state.user.username)}!`,
      "Một góc nhìn rõ ràng hơn cho mọi quyết định kinh doanh.",
      button("＋ Kết nối dữ liệu", "data"),
    ) +
    (state.analysis
      ? `${kpis()}<section class="card"><div class="row between"><h2>Doanh thu theo thời gian</h2><span class="tag">${esc(state.name)}</span></div>${trend()}</section><div class="grid2 section-gap"><section class="card"><h2>Top sản phẩm</h2>${products()}</section><section class="card"><h2>Chất lượng dữ liệu</h2><div class="donut" data-label="${number(state.analysis.quality.score * 100)}%" style="background:conic-gradient(#8072e3 ${state.analysis.quality.score * 360}deg,#eeedf9 0)"></div><p style="text-align:center">${number(state.analysis.profile.row_count)} dòng · ${number(state.analysis.quality.duplicates.rows)} đơn trùng</p></section></div>`
      : `<section class="hero"><div><span class="tag">BẮT ĐẦU HÀNH TRÌNH DỮ LIỆU</span><h2 class="section-gap">Chưa có dữ liệu?<br>Hãy bắt đầu ngay!</h2><p>Kết nối dữ liệu của bạn để tạo báo cáo, phân tích AI và khám phá insight cho doanh nghiệp.</p>${button("Kết nối dữ liệu ngay →", "data")}<br>${button("Hoặc khám phá bằng dữ liệu mẫu →", "sample", "ghost")}</div><div class="hero-art">${robot()}<div class="mini-chart">${[30, 50, 40, 75, 90].map((h) => `<i style="height:${h}%"></i>`).join("")}</div></div></section><h2 class="section-gap">Bắt đầu trong 3 bước đơn giản</h2><div class="steps">${[
          ["1", "Kết nối dữ liệu", "Tải tệp CSV hoặc JSON từ máy tính."],
          [
            "2",
            "Khám phá và phân tích",
            "Xem biểu đồ, chỉ số và hỏi trợ lý AI.",
          ],
          ["3", "Đưa ra quyết định", "Xuất báo cáo và chia sẻ kết quả."],
        ]
          .map(
            ([n, t, d]) =>
              `<div class="step"><b>${n}</b><div><strong>${t}</strong><p>${d}</p></div></div>`,
          )
          .join(
            "",
          )}</div><h2 class="section-gap">Nguồn dữ liệu</h2><div class="sources">${[
          ["▤", "CSV", "Sẵn sàng"],
          ["{}", "JSON", "Sẵn sàng"],
          ["▦", "Excel", "Chưa có connector"],
          ["▥", "Google Sheets", "Chưa có connector"],
          ["▱", "SQL Server", "Chưa có connector"],
          ["⌁", "API", "Chưa có connector"],
        ]
          .map(
            ([i, t, s]) =>
              `<div class="source"><span>${i}</span><strong>${t}</strong><small>${s}</small></div>`,
          )
          .join(
            "",
          )}</div><div class="tip section-gap row between"><span>✧ Dùng dữ liệu mẫu để thử trọn luồng phân tích qua API.</span>${button("Dùng dữ liệu mẫu →", "sample")}</div>`)
  );
}
function filters() {
  const options = [...new Set(state.rows.map((r) => r.product))];
  return `<form data-form="filter"><h2>Bộ lọc báo cáo</h2>${field("Từ ngày", "from", "date", `value="${esc(state.filter.from || "")}"`).replace(" required", "")}${field("Đến ngày", "to", "date", `value="${esc(state.filter.to || "")}"`).replace(" required", "")}<label>Sản phẩm<select name="product"><option value="">Tất cả sản phẩm</option>${options.map((p) => `<option ${p === state.filter.product ? "selected" : ""}>${esc(p)}</option>`).join("")}</select></label><button class="primary" ${!state.rows.length ? "disabled" : ""}>Áp dụng bộ lọc</button> ${button("Đặt lại", "reset-filter", "ghost")}</form>`;
}
function reports() {
  return (
    heading("Báo cáo", "Tạo và xuất báo cáo kinh doanh từ dữ liệu hiện tại.") +
    `<div class="tabs"><button class="selected">▥ Báo cáo doanh thu</button><span class="tag">Báo cáo khách hàng / nhân sự: cần API bổ sung</span></div>${kpis()}<div class="split"><div class="stack"><section class="card"><h2>Biểu đồ doanh thu theo thời gian</h2>${trend()}</section><section class="card"><h2>Báo cáo đã xuất trong phiên</h2>${state.reports.length ? table(state.reports) : "<p>Chưa có báo cáo nào. Chọn định dạng bên phải để xuất.</p>"}</section></div><aside class="stack"><section class="card">${filters()}</section><section class="card"><h2>Xuất báo cáo</h2><div class="export-buttons">${["pdf", "xlsx", "pptx", "json", "csv", "html"].map((f) => `<button data-export="${f}" ${!state.analysis ? "disabled" : ""}><b>▤</b>${f.toUpperCase()}</button>`).join("")}</div></section><div class="tip">✧ Báo cáo được tạo bởi backend từ các dòng sau khi lọc. Lịch sử này chỉ tồn tại trong phiên.</div></aside></div>`
  );
}
function table(rows) {
  if (!rows.length) return "<p>Không có dòng phù hợp.</p>";
  const keys = Object.keys(rows[0]);
  return `<div class="table-wrap"><table><thead><tr>${keys.map((k) => `<th>${esc(k)}</th>`).join("")}</tr></thead><tbody>${rows
    .slice(0, 50)
    .map(
      (r) =>
        `<tr>${keys.map((k) => `<td>${esc(typeof r[k] === "object" ? JSON.stringify(r[k]) : r[k])}</td>`).join("")}</tr>`,
    )
    .join(
      "",
    )}</tbody></table></div>${rows.length > 50 ? `<p><small>Hiển thị 50/${number(rows.length)} dòng đầu.</small></p>` : ""}`;
}
function dataView() {
  return (
    heading(
      "Dữ liệu",
      "Quản lý dữ liệu trong phiên làm việc và kiểm tra chất lượng.",
      state.analysis ? button("Xóa khỏi phiên", "clear-data", "ghost") : "",
    ) +
    `<div class="split"><div class="stack"><section class="card"><form data-form="upload" class="dropzone"><div class="empty-symbol">⇧</div><h2>Tải dữ liệu của bạn</h2><p>CSV hoặc JSON · UTF-8 · Tối đa 10 MiB<br>Hỗ trợ tự động nhận diện từ điển ngữ nghĩa 38 cột (Anh/Việt) &amp; 5 vai trò chuẩn: date, order_id, product, revenue, cost</p><label>Tệp dữ liệu<input name="file" type="file" accept=".csv,.json" required></label><button class="primary">Tải lên & phân tích</button> ${button("Dùng mẫu", "sample", "ghost")}</form></section><section class="card"><div class="row between"><h2>Dữ liệu hiện tại</h2><span class="tag">${state.analysis ? esc(state.name) : "Chưa tải"}</span></div>${state.rows.length ? table(state.rows) : empty()}</section>${state.analysis ? `<section class="card"><h2>Schema & thống kê</h2><details><summary>Kiểu dữ liệu và quan hệ</summary>${jsonBlock(state.analysis.schema)}</details><details><summary>Profiling: phân bố, min, max, trung bình</summary>${jsonBlock(state.analysis.profile)}</details><details><summary>Chi tiết chất lượng</summary>${jsonBlock(state.analysis.quality)}</details></section>` : ""}<section class="card"><h2>Suy luận quan hệ nhiều bảng</h2><form data-form="relations"><label>JSON: {"tables": {"orders": [...], "customers": [...]}}<textarea name="tables" required placeholder='{"tables":{"orders":[{"customer_id":"C1"}],"customers":[{"customer_id":"C1"}]}}'></textarea></label><button class="primary">Phân tích quan hệ</button></form>${state.result?.kind === "relations" ? jsonBlock(state.result.data) : ""}</section></div><aside class="stack"><section class="card"><h2>Trạng thái dữ liệu</h2><p>${state.rows.length ? `${number(state.rows.length)} dòng đã tải` : "Chưa có nguồn dữ liệu"}</p><span class="tag ${state.demo ? "orange" : "green"}">${state.demo ? "Dữ liệu mẫu" : "Dữ liệu của bạn"}</span><div class="notice section-gap">Dữ liệu lưu trong bộ nhớ phiên. Tải lại trang hoặc đăng xuất sẽ xóa dữ liệu khỏi giao diện.</div></section><section class="card"><h2>Tệp mẫu</h2><p>Đúng schema backend, sẵn sàng để tải lên.</p>${button("↓ Tải CSV mẫu", "download-sample", "ghost")}</section></aside></div>`
  );
}
function chat() {
  return (
    heading(
      "Chat với AI",
      "Hỏi về số liệu của bạn, nhận câu trả lời dựa trên dashboard.",
    ) +
    `<div class="chat-layout"><section class="card chat-panel"><div class="row between"><h2>✧ Trợ lý phân tích</h2><span class="tag">${state.analysis ? "Có ngữ cảnh dữ liệu" : "Chưa có dữ liệu"}</span></div><div class="messages"><div class="bubble">Xin chào ${esc(state.user.username)}! Tôi có thể giúp bạn phân tích doanh thu, sản phẩm và chất lượng dữ liệu. ${state.analysis ? "Bạn muốn tìm hiểu điều gì?" : "Hãy tải dữ liệu trước để bắt đầu."}</div>${state.messages.map((m) => `<div class="bubble ${m.role === "user" ? "user" : ""}">${esc(m.text)}${m.source ? `<small>Nguồn: ${esc(m.source)}</small>` : ""}</div>`).join("")}</div><form class="chat-input" data-form="chat"><input name="question" maxlength="2000" placeholder="Hỏi về doanh thu, lợi nhuận, sản phẩm…" aria-label="Câu hỏi" required ${!state.analysis ? "disabled" : ""}><select name="mode" aria-label="Chế độ" style="width:110px"><option value="query">Chat AI</option><option value="sql">SQL</option></select><button class="primary" ${!state.analysis ? "disabled" : ""}>Gửi ↗</button></form></section><aside class="stack"><section class="card"><h2>Gợi ý cho bạn</h2><div class="quick">${["Tổng doanh thu là bao nhiêu?", "Sản phẩm nào có doanh thu cao nhất?", "Lợi nhuận của dữ liệu hiện tại?", "Chất lượng dữ liệu như thế nào?"].map((q) => `<button data-question="${q}" ${!state.analysis ? "disabled" : ""}>✧ ${q}</button>`).join("")}</div></section><div class="tip">Câu trả lời có thể đến từ chế độ deterministic. Nhãn nguồn dưới mỗi câu trả lời cho biết provider thực tế.</div><section class="card"><h2>Text-to-SQL</h2><p>Chế độ SQL trả câu lệnh SELECT đã kiểm tra. Giao diện không thực thi SQL tùy ý.</p></section></aside></div>`
  );
}
function synthetic() {
  if (!canGenerate(state.user))
    return '<div class="error">Bạn không có quyền truy cập.</div>';
  return (
    heading(
      "Dữ liệu tổng hợp",
      "Sinh và kiểm định dữ liệu từ tập dữ liệu hiện tại.",
    ) +
    `<div class="grid2"><section class="card"><form data-form="synthetic"><label>Mô hình<select name="model">${["bootstrap", "gaussian_copula", "ctgan", "copulagan", "llm_agent"].map((m) => `<option>${m}</option>`).join("")}</select></label>${field("Số dòng cần sinh", "count", "number", 'min="1" max="100000" value="100"')}${field("Seed", "seed", "number", 'value="42"')}<label>Cột mục tiêu TSTR (không bắt buộc)<input name="target_column" placeholder="revenue"></label><button class="primary" ${!state.rows.length ? "disabled" : ""}>Sinh & kiểm định</button></form><p class="section-gap">CTGAN/Copula cần requirements-ai. LLM Agent cần provider thật. Tập lớn có thể vượt thời gian chờ.</p></section><section class="card">${state.result?.kind === "synthetic" ? `<h2>Kết quả kiểm định</h2>${jsonBlock(state.result.data.validation)}${button("Tải JSON tổng hợp", "download-synthetic")}` : empty("Sẵn sàng tạo dữ liệu mới", "Tải dữ liệu ở mục Dữ liệu, sau đó chọn mô hình.")}</section></div>`
  );
}
function admin() {
  if (!canAdmin(state.user))
    return '<div class="error">Chỉ quản trị viên có thể truy cập.</div>';
  return (
    heading(
      "Quản trị tài khoản",
      "Phê duyệt yêu cầu và cấp tài khoản nhân viên.",
      button("↻ Tải yêu cầu", "load-requests"),
    ) +
    `<div class="notice">Backend hiện có danh sách yêu cầu đăng ký, chưa có API danh sách toàn bộ nhân viên. Quyền và phạm vi dữ liệu được cấp trong bước provision.</div><section class="card section-gap"><h2>Yêu cầu đăng ký</h2><div class="table-wrap"><table><thead><tr><th>ID</th><th>Nhân viên</th><th>Họ tên</th><th>Phòng ban</th><th>Trạng thái</th><th>Thao tác</th></tr></thead><tbody>${state.requests.map((r) => `<tr><td>${r.id}</td><td>${esc(r.employee_id)}</td><td>${esc(r.full_name)}</td><td>${esc(r.department)}</td><td><span class="tag">${esc(r.status)}</span></td><td>${r.status === "PENDING" ? `<button data-approve="${r.id}">Duyệt</button> <button data-reject="${r.id}" class="danger">Từ chối</button>` : r.status === "APPROVED" ? `<button data-provision="${r.id}">Cấp tài khoản</button>` : "—"}</td></tr>`).join("")}</tbody></table></div>${!state.requests.length ? '<p class="section-gap">Chưa tải hoặc chưa có yêu cầu. Nhấn “Tải yêu cầu” để cập nhật.</p>' : ""}</section><div class="grid2 section-gap"><section class="card"><h2>Cấp tài khoản đã phê duyệt</h2><form data-form="provision">${field("ID yêu cầu", "registration_request_id", "number", 'min="1"')}${field("Mật khẩu tạm", "temporary_password", "password", 'minlength="8" maxlength="256" autocomplete="new-password"')}<label>Vai trò<select name="role"><option>user</option><option>manager</option><option>admin</option></select></label><label>Phạm vi<select name="data_scope"><option>own</option><option>department</option><option>all</option></select></label><p>Quyền mặc định theo vai trò sẽ được gửi. Phạm vi all chỉ dành cho admin.</p><button class="primary">Cấp tài khoản</button></form></section><section class="card"><h2>Đổi vai trò tài khoản</h2><form data-form="role">${field("User ID", "user_id", "number", 'min="1"')}<label>Vai trò mới<select name="role"><option>user</option><option>manager</option><option>admin</option></select></label><button class="primary">Cập nhật vai trò</button></form><p class="section-gap">Thay đổi role làm token cũ mất hiệu lực. Nhân viên cần đăng nhập lại.</p>${state.result?.kind === "admin" ? jsonBlock(state.result.data) : ""}</section></div>`
  );
}
function settings() {
  return (
    heading("Cài đặt", "Cấu hình giao diện và kết nối cho trình duyệt này.") +
    `<div class="grid2"><section class="card"><h2>Kết nối backend</h2><form data-form="settings"><label>API Base URL<input name="base" type="url" required value="${esc(api.base)}"></label><button class="primary">Lưu kết nối</button> ${button("Kiểm tra kết nối", "health", "ghost")}</form><p class="section-gap">Origin frontend mặc định: http://localhost:5173. Backend phải cho phép origin này trong CORS_ORIGINS.</p></section><section class="card"><h2>Thông tin phiên</h2><p>Tài khoản: ${esc(state.user.username)}<br>Vai trò: ${esc(state.user.role)}<br>Phạm vi: ${esc(state.user.data_scope)}</p><details><summary>Quyền được cấp</summary>${jsonBlock(state.user.permissions)}</details><p class="section-gap">Token chỉ lưu trong bộ nhớ. Tải lại trang cần đăng nhập lại.</p></section><section class="card"><h2>Những tích hợp tiếp theo</h2><p>Email, lịch báo cáo, thông báo, đồng bộ HR, quản lý thuê bao và connector Google Sheets/SQL chưa có API. Không thay đổi cài đặt hệ thống từ giao diện này.</p></section></div>`
  );
}
function pageView() {
  switch (state.page) {
    case "overview":
      return overview();
    case "reports":
      return reports();
    case "data":
      return dataView();
    case "chat":
      return chat();
    case "synthetic":
      return synthetic();
    case "admin":
      return admin();
    case "settings":
      return settings();
    case "products":
      return (
        heading("Sản phẩm", "Xếp hạng theo doanh thu trong dữ liệu hiện tại.") +
        `<section class="card">${products()}</section>`
      );
    case "finance":
      return (
        heading("Tài chính", "Các chỉ số được tính từ dữ liệu sau lọc.") +
        kpis() +
        `<section class="card">${state.analysis ? table(Object.entries(state.analysis.kpis).map(([metric, value]) => ({ metric, value: value ?? "Chưa đủ dữ liệu" }))) : empty()}</section>`
      );
    default:
      return overview();
  }
}
function render() {
  root.innerHTML = state.user ? shell() : authView();
  if (state.result?.kind === "reject") {
    root
      .querySelector("main")
      .insertAdjacentHTML(
        "afterbegin",
        `<section class="card section-gap"><h2>Từ chối yêu cầu #${Number(state.result.id)}</h2><form data-form="reject"><label>Lý do từ chối<textarea name="rejection_reason" maxlength="500" required></textarea></label><button class="danger">Xác nhận từ chối</button> ${button("Hủy", "cancel-reject", "ghost")}</form></section>`,
      );
  }
}
async function analyzeRows(rows) {
  return api.post(
    "/datasets/analyze?filename=dataset.json",
    JSON.stringify(rows),
    { raw: true },
  );
}
async function loadRows(rows, name, demo) {
  const analysis = await analyzeRows(rows);
  state.rows = rows;
  state.analysis = analysis;
  state.name = name;
  state.demo = demo;
  state.filter = {};
  state.messages = [];
  state.result = null;
  toast(`Đã phân tích ${rows.length} dòng qua API.`);
}
function selectedRows() {
  return filterRows(state.rows, state.filter);
}
const rolePermissions = {
  user: [
    "dashboard:view",
    "dataset:upload",
    "dataset:view",
    "kpi:view",
    "chart:view",
    "chat:use",
    "report:view",
  ],
  manager: [
    "dashboard:view",
    "dataset:upload",
    "dataset:view",
    "kpi:view",
    "chart:view",
    "chat:use",
    "report:view",
    "report:export",
    "synthetic:generate",
  ],
  admin: [
    "dashboard:view",
    "dataset:upload",
    "dataset:view",
    "kpi:view",
    "chart:view",
    "chat:use",
    "report:view",
    "report:export",
    "synthetic:generate",
    "user:manage",
  ],
};
root.addEventListener("submit", (event) => {
  event.preventDefault();
  const form = event.target;
  const data = Object.fromEntries(new FormData(form));
  const kind = form.dataset.form;
  run(async () => {
    if (kind === "login") {
      const token = await api.post("/auth/login", data, { token: "" });
      if (token.purpose === "activation") {
        state.activation = token.access_token;
        state.auth = "activate";
      } else {
        api.token = token.access_token;
        state.user = await api.request("/auth/me");
        state.page = "overview";
      }
    }
    if (kind === "register") {
      await api.post("/auth/register-request", data, { token: "" });
      state.auth = "registered";
    }
    if (kind === "activate") {
      if (data.new_password !== data.confirm_password)
        throw new Error("Hai mật khẩu không khớp.");
      await api.post("/auth/activate", data, { token: state.activation });
      state.activation = "";
      state.auth = "login";
      toast("Kích hoạt thành công. Đăng nhập lại bằng mật khẩu mới.");
    }
    if (kind === "upload") {
      const file = data.file;
      if (!file.size || file.size > 10485760)
        throw new Error("Tệp phải từ 1 byte đến 10 MiB.");
      const text = await file.text();
      const rows = parseDataset(text, file.name);
      const analysis = await api.post(
        "/datasets/analyze?filename=" + encodeURIComponent(file.name),
        text,
        { raw: true },
      );
      state.rows = rows;
      state.analysis = analysis;
      state.name = file.name;
      state.demo = false;
      state.filter = {};
      state.messages = [];
      state.result = null;
      toast("Tải dữ liệu thành công.");
    }
    if (kind === "filter") {
      if (data.from && data.to && data.from > data.to)
        throw new Error("Ngày bắt đầu phải trước ngày kết thúc.");
      const rows = filterRows(state.rows, data);
      if (!rows.length) throw new Error("Không có dữ liệu phù hợp bộ lọc.");
      state.analysis = await analyzeRows(rows);
      state.filter = data;
    }
    if (kind === "chat") {
      const payload = { rows: selectedRows(), question: data.question };
      const response = await api.post("/chat/" + data.mode, payload);
      state.messages.push(
        { role: "user", text: data.question },
        {
          role: "assistant",
          text: response.answer || response.sql,
          source: response.provider || response.source || "deterministic",
        },
      );
    }
    if (kind === "synthetic") {
      const response = await api.post("/synthetic/generate", {
        rows: selectedRows(),
        count: Number(data.count),
        seed: Number(data.seed),
        model: data.model,
        target_column: data.target_column || null,
      });
      state.result = { kind: "synthetic", data: response };
    }
    if (kind === "relations") {
      const response = await api.post(
        "/schema/infer-relations",
        JSON.parse(data.tables),
      );
      state.result = { kind: "relations", data: response };
    }
    if (kind === "provision") {
      if (data.data_scope === "all" && data.role !== "admin")
        throw new Error("Phạm vi all chỉ dành cho admin.");
      const response = await api.post("/admin/users/provision", {
        ...data,
        registration_request_id: Number(data.registration_request_id),
        permissions: rolePermissions[data.role],
      });
      state.result = { kind: "admin", data: response };
      toast("Đã cấp tài khoản. Chuyển mật khẩu tạm qua kênh nội bộ an toàn.");
    }
    if (kind === "role") {
      const response = await api.post(
        `/auth/users/${Number(data.user_id)}/role`,
        { role: data.role },
      );
      state.result = { kind: "admin", data: response };
      toast("Đã cập nhật vai trò.");
    }
    if (kind === "reject") {
      if (!data.rejection_reason.trim())
        throw new Error("Lý do không được để trống.");
      await api.post(
        `/admin/registration-requests/${Number(state.result.id)}/reject`,
        data,
      );
      state.requests = await api.request("/admin/registration-requests");
      state.result = null;
      toast("Đã từ chối yêu cầu.");
    }
    if (kind === "settings") {
      const url = new URL(data.base);
      if (
        !["http:", "https:"].includes(url.protocol) ||
        url.username ||
        url.password ||
        url.search ||
        url.hash
      )
        throw new Error(
          "Nhập URL HTTP(S) hợp lệ, không kèm credentials/query.",
        );
      const next = url.href.replace(/\/$/, "");
      if (next !== api.base) {
        api.base = next;
        localStorage.setItem("candy.api", next);
        resetSession();
        toast("Đã đổi kết nối. Đăng nhập lại để sử dụng backend mới.");
      }
    }
    if (kind === "search") {
      const match = pages.find(([, , label]) =>
        label
          .toLocaleLowerCase("vi")
          .includes(data.search.toLocaleLowerCase("vi")),
      );
      if (!match) throw new Error("Không tìm thấy trang phù hợp.");
      if (
        (match[0] === "admin" && !canAdmin(state.user)) ||
        (match[0] === "synthetic" && !canGenerate(state.user))
      )
        throw new Error("Bạn không có quyền truy cập trang này.");
      state.page = match[0];
    }
  });
});
root.addEventListener("click", (event) => {
  const el = event.target.closest("button");
  if (!el || state.busy) return;
  if (el.dataset.page) {
    state.page = el.dataset.page;
    state.error = "";
    state.result = null;
    render();
    return;
  }
  if (el.dataset.question) {
    const input = root.querySelector("[name=question]");
    input.value = el.dataset.question;
    input.focus();
    return;
  }
  if (el.dataset.provision) {
    root.querySelector("[name=registration_request_id]").value =
      el.dataset.provision;
    root.querySelector("[name=temporary_password]").focus();
    return;
  }
  if (el.dataset.export) {
    run(async () => {
      const format = el.dataset.export;
      const blob = await api.post(
        `/reports/export?format=${format}`,
        { rows: selectedRows() },
        { blob: true },
      );
      saveFile(blob, `report.${format}`);
      state.reports.unshift({
        name: `Báo cáo ${state.name}`,
        format: format.toUpperCase(),
        time: new Date().toLocaleString("vi-VN"),
        status: "Đã tải",
      });
      toast("Báo cáo đã được tạo và tải xuống.");
    });
    return;
  }
  if (el.dataset.reject) {
    state.result = { kind: "reject", id: Number(el.dataset.reject) };
    render();
    return;
  }
  if (el.dataset.approve) {
    run(async () => {
      await api.post(
        `/admin/registration-requests/${Number(el.dataset.approve)}/approve`,
        {},
      );
      state.requests = await api.request("/admin/registration-requests");
      toast("Đã duyệt yêu cầu.");
    });
    return;
  }
  const action = el.dataset.action;
  if (!action) return;
  if (["login", "register"].includes(action)) {
    state.auth = action;
    state.error = "";
    render();
    return;
  }
  if (pages.some(([key]) => key === action)) {
    state.page = action;
    state.error = "";
    render();
    return;
  }
  if (action === "menu") {
    root.querySelector(".sidebar").classList.toggle("open");
    return;
  }
  if (action === "cancel-reject") {
    state.result = null;
    render();
    return;
  }
  if (action === "logout") {
    resetSession();
    render();
    return;
  }
  if (action === "forgot") {
    toast(
      "Liên hệ quản trị viên để hỗ trợ mật khẩu. Backend chưa có chức năng tự đặt lại.",
    );
    return;
  }
  if (action === "connection") {
    state.auth = "connection";
    state.error = "";
    render();
    return;
  }
  if (action === "download-sample") {
    const keys = Object.keys(sampleRows[0]);
    saveFile(
      new Blob(
        [
          "\uFEFF" +
            keys.join(",") +
            "\n" +
            sampleRows
              .map((r) =>
                keys
                  .map((k) => '"' + String(r[k]).replaceAll('"', '""') + '"')
                  .join(","),
              )
              .join("\n"),
        ],
        { type: "text/csv;charset=utf-8" },
      ),
      "sample.csv",
    );
    return;
  }
  if (action === "download-synthetic") {
    saveFile(
      new Blob([JSON.stringify(state.result.data.rows, null, 2)], {
        type: "application/json",
      }),
      "synthetic.json",
    );
    return;
  }
  if (action === "clear-data") {
    state.rows = [];
    state.analysis = null;
    state.name = "";
    state.demo = false;
    state.messages = [];
    state.result = null;
    state.filter = {};
    render();
    return;
  }
  run(async () => {
    if (action === "sample")
      await loadRows(sampleRows, "Dữ liệu mẫu · 24 đơn", true);
    if (action === "load-requests")
      state.requests = await api.request("/admin/registration-requests");
    if (action === "health") {
      const r = await api.request("/health", { token: "" });
      toast(`Backend: ${r.status} · v${r.version}`);
    }
    if (action === "reset-filter") {
      state.analysis = await analyzeRows(state.rows);
      state.filter = {};
    }
  });
});
render();

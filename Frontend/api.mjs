import { errorMessage } from "./core.mjs";
export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}
export class ApiClient {
  constructor(base = "http://127.0.0.1:8000") {
    this.base = base;
    this.token = "";
  }
  async request(
    path,
    {
      method = "GET",
      body,
      raw = false,
      blob = false,
      token = this.token,
    } = {},
  ) {
    const headers = {};
    if (token) headers.Authorization = `Bearer ${token}`;
    if (body !== undefined)
      headers["Content-Type"] = raw
        ? "application/octet-stream"
        : "application/json";
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 120000);
    try {
      const response = await fetch(this.base + path, {
        method,
        headers,
        body:
          body === undefined ? undefined : raw ? body : JSON.stringify(body),
        signal: controller.signal,
      });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new ApiError(errorMessage(data), response.status);
      }
      if (response.status === 204) return null;
      return blob ? response.blob() : response.json();
    } catch (error) {
      if (error instanceof ApiError) throw error;
      throw new Error(
        error.name === "AbortError"
          ? "Yêu cầu quá 120 giây. Hãy thử với dữ liệu nhỏ hơn."
          : "Không kết nối được API. Kiểm tra backend và CORS tại phần Cài đặt kết nối.",
      );
    } finally {
      clearTimeout(timer);
    }
  }
  post(path, body, options = {}) {
    return this.request(path, { method: "POST", body, ...options });
  }
}

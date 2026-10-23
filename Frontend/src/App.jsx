import React from 'react';
import { Sparkles, Database, CheckCircle2 } from 'lucide-react';

export default function App() {
  return (
    <div className="min-h-screen bg-brandBg text-brandText flex flex-col items-center justify-center p-6">
      <div className="max-w-xl w-full bg-surface rounded-2xl shadow-sm border border-line p-8 space-y-6">
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 rounded-xl bg-primary-light flex items-center justify-center text-primary">
            <Sparkles className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-brandText">Code Candy – AI BI Dashboard</h1>
            <p className="text-xs text-muted">React + Vite + TailwindCSS Infrastructure (F-01)</p>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-primary-light/50 border border-primary/20 space-y-2">
          <div className="flex items-center text-primary font-semibold text-sm">
            <CheckCircle2 className="w-4 h-4 mr-2" />
            Nền tảng Frontend khởi tạo thành công
          </div>
          <p className="text-xs text-muted leading-relaxed">
            Hệ thống đóng gói Vite, cấu hình TailwindCSS kế thừa mã màu chuẩn và Proxy API (/api, /auth) đã sẵn sàng cho các bước tiếp theo.
          </p>
        </div>

        <div className="grid grid-cols-2 gap-3 pt-2 text-xs">
          <div className="p-3 rounded-lg border border-line bg-brandBg/50">
            <span className="text-muted block">Vite Dev Port</span>
            <span className="font-semibold text-brandText">5173</span>
          </div>
          <div className="p-3 rounded-lg border border-line bg-brandBg/50">
            <span className="text-muted block">Backend Proxy</span>
            <span className="font-semibold text-brandText">127.0.0.1:8000</span>
          </div>
        </div>
      </div>
    </div>
  );
}


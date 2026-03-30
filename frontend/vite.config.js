import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "0.0.0.0", // 노트북 등 외부 기기 접속 허용 (필수)
    port: 3000,
    proxy: {
      // 프론트에서 '/api'로 시작하는 요청을 보내면 8000번 포트로 우회
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
      // '/recommend' 라우터가 있다면 이 부분도 추가
      "/recommend": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
});

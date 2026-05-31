import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Dev proxy: /api -> FastAPI on :8000 so the frontend can call it same-origin.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "node",
    include: ["src/**/*.test.{js,jsx}"],
  },
  server: {
    port: 5173,
    proxy: {
      "/bennes": "http://localhost:8000",
      "/alertes": "http://localhost:8000",
      "/sync": "http://localhost:8000",
      "/health": "http://localhost:8000",
    },
  },
});

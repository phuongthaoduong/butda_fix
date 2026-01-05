import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  resolve: {
    dedupe: ["react", "react-dom"]
  },
  server: {
    port: 5173,
    hmr: {
      host: "localhost",
      clientPort: 5173
    },
    proxy: {
      "/api": {
        target: "http://localhost:8001",
        changeOrigin: true
      }
    }
  }
});
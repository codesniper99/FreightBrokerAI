import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  server: {
    proxy: {
      // forward unknown requests to FastAPI when developing
      "/negotiate/start": "http://localhost:8000",
      "/negotiate/start/v2": "http://localhost:8000",
      "/negotiate/result": "http://localhost:8000",
      "/mc_key": "http://localhost:8000",
      "/webhook": "http://localhost:8000",
      "/result": "http://localhost:8000",
      "/start_clean": "http://localhost:8000",
      "/api": "http://localhost:8000",
      "/dashboard": "http://localhost:8000",
      "/negotiations_dashboard": "http://localhost:8000",
    },
  },
});
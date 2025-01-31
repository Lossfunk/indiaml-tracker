import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import viteTsconfigPaths from "vite-tsconfig-paths";
import svgr from "vite-plugin-svgr";
import mkcert from'vite-plugin-mkcert'

// https://vitejs.dev/config/
export default defineConfig({
  server: {
    https: false
  },
  plugins: [
    svgr({
      svgrOptions: { exportType: "default" },
      include: ["**/*.svg", "**/*.svg?react"],
    }),
    react(),
    viteTsconfigPaths(),
    // mkcert(),
  ],
});

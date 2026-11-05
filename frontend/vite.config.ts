/// <reference types="vitest/config" />
import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  // Chemins relatifs : le build fonctionne aussi une fois embarqué dans Tauri (phase 7).
  base: "./",
  // fs.allow ".." : la page À propos lit le CHANGELOG.md à la racine du projet.
  server: { port: 5173, strictPort: true, fs: { allow: [".."] } },
  // Application de bureau chargée depuis le disque (pas de téléchargement) :
  // un fichier JS d'environ 600 Ko (surtout Recharts) n'a pas d'impact sensible.
  build: { chunkSizeWarningLimit: 1000 },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
  },
});

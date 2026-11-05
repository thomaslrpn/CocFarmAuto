/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** URL du backend (défaut : http://127.0.0.1:8765) */
  readonly VITE_API_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

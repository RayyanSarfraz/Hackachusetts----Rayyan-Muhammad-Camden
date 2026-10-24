/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** When 'true', the app routes API calls through the Django backend. */
  readonly VITE_USE_HTTP_API?: string
  /** Override the API base path (default '/api', proxied by Vite in dev). */
  readonly VITE_API_BASE?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

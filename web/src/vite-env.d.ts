// Tells TypeScript which VITE_* variables exist on import.meta.env.
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string;
}

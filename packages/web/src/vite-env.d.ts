/// <reference types="vite/client" />
/// <reference types="vitest/globals" />

declare const __APP_VERSION__: string;

declare module '*.css' {
  const content: string;
  export default content;
}

import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#111827",
        muted: "#6b7280",
        surface: "#f8fafc",
        accent: "#2563eb",
        accentDark: "#1e40af",
      },
    },
  },
  plugins: [],
};

export default config;

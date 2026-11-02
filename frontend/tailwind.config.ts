import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Barlow Semi Condensed"', "ui-sans-serif", "system-ui", "-apple-system", "Helvetica", "Arial", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "SFMono-Regular", "Menlo", "monospace"],
      },
      boxShadow: {
        card: "0 1px 0 rgba(30,64,175,0.05), 0 16px 40px -20px rgba(37,99,235,0.30)",
        pop: "0 8px 24px -12px rgba(37,99,235,0.55)",
      },
    },
  },
  plugins: [],
} satisfies Config;

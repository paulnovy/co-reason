import type { Config } from "tailwindcss";

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        variable: {
          hard: '#10b981',      // green
          user: '#3b82f6',      // blue
          ai: '#f59e0b',        // orange
          mixed: '#8b5cf6',     // purple
        }
      }
    },
  },
  plugins: [],
} satisfies Config;

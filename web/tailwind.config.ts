import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          dark: "#0F172A",
          panel: "#1E293B",
          border: "#334155",
          accent: "#38BDF8",
          hot: "#EF4444",
          cool: "#3B82F6",
        },
      },
    },
  },
  plugins: [],
};
export default config;

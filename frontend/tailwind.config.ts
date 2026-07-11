import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      colors: {
        navy: {
          900: "#060b14",
          800: "#0c1526",
          700: "#111f38",
          600: "#1a2d4d",
        },
        local: "#22c55e",
        cloud: "#3b82f6",
      },
      animation: {
        "pulse-dot": "pulse 1.5s cubic-bezier(0.4,0,0.6,1) infinite",
        "fade-in": "fadeIn .4s ease-out",
        "slide-up": "slideUp .4s ease-out",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { transform: "translateY(10px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
      },
    },
  },
  plugins: [],
};
export default config;
import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      fontFamily: {
        raleway: ["Raleway", "Arial", "sans-serif"],
      },
      colors: {
        brand: {
          ink: "#141414",
          paper: "#ffffff",
          lime: "#c1f11d",
          blue: "#3dedf1",
          coral: "#ff8e70",
          purple: "#b4b0ef",
        },
      },
      borderRadius: {
        xl: "1.9rem",
        lg: "1.45rem",
        md: "1.05rem",
        sm: "0.9rem",
        pill: "999px",
      },
      boxShadow: {
        surface: "0 18px 50px rgba(20, 20, 20, 0.07)",
      },
    },
  },
  plugins: [],
};

export default config;

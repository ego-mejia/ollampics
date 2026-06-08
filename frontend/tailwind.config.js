/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx,js,jsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        // Brand palette — same in both themes
        brand: {
          blue:    "#3D49E4",
          magenta: "#E5358F",
          lime:    "#D9F764",
          yellow:  "#F4C84A",
          sky:     "#8AA7E8",
          red:     "#E5402F",
          green:   "#5DBA32",
          orange:  "#F2A340",
          purple:  "#8C42D8",
        },
        // Theme-aware semantic tokens, driven by CSS vars in index.css
        bg:              "rgb(var(--bg) / <alpha-value>)",
        card:            "rgb(var(--card) / <alpha-value>)",
        elev:            "rgb(var(--elev) / <alpha-value>)",
        border:          "rgb(var(--border) / <alpha-value>)",
        "border-soft":   "rgb(var(--border-soft) / <alpha-value>)",
        fg:              "rgb(var(--fg) / <alpha-value>)",
        "fg-muted":      "rgb(var(--fg-muted) / <alpha-value>)",
        "fg-dim":        "rgb(var(--fg-dim) / <alpha-value>)",
        // Backwards-compat aliases (existing classes don't break)
        accent:       "#3D49E4",
        success:      "#5DBA32",
      },
    },
  },
  plugins: [],
};

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./src/**/*.{html,js,svelte,ts}"],
  theme: {
    extend: {},
  },
  plugins: [require("@tailwindcss/typography"), require("daisyui")],
  daisyui: {
    themes: [
      {
        kilntheme: {
          primary: "#ffffff",
          "primary-content": "#161616",
          secondary: "#ffffff",
          "secondary-content": "#161616",
          accent: "#ffffff",
          "accent-content": "#161616",
          neutral: "#000000",
          "neutral-content": "#bebebe",
          "base-100": "#ffffff",
          "base-200": "#F5F5F5",
          "base-300": "#bebebe",
          "base-content": "#161616",
          info: "#a6ffff",
          "info-content": "#0a1616",
          success: "#8effe4",
          "success-content": "#071612",
          warning: "#fff590",
          "warning-content": "#161507",
          error: "#ffd7c5",
          "error-content": "#16110e",
        },
      },
    ],
  },
}

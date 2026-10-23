/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#5651e8',
          hover: '#4843d0',
          light: '#eeeff9',
        },
        surface: {
          DEFAULT: '#ffffff',
          dark: '#252940',
        },
        line: {
          DEFAULT: '#eceef6',
          dark: '#363b56',
        },
        muted: {
          DEFAULT: '#858aa1',
          dark: '#b7bcd5',
        },
        brandBg: {
          DEFAULT: '#f5f6fc',
          dark: '#1d2136',
        },
        brandText: {
          DEFAULT: '#202640',
          dark: '#eef0ff',
        },
      },
      fontFamily: {
        sans: ['Inter', 'Segoe UI', 'Arial', 'sans-serif'],
      },
    },
  },
  plugins: [],
};


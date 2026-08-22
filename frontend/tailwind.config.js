/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0f7ff',
          100: '#e0effe',
          200: '#bae0fd',
          300: '#7cc7fd',
          400: '#36a9fa',
          500: '#0c8ce9',
          600: '#006ec7',
          700: '#0258a2',
          800: '#064b85',
          900: '#0b3f6f',
          950: '#07284a',
        },
      },
    },
  },
  plugins: [],
}

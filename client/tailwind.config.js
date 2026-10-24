/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        navy: {
          DEFAULT: '#10263D',
          light: '#1b3a5c',
          dark: '#0b1b2c',
        },
        teal: {
          DEFAULT: '#0D9488',
          light: '#14b8a6',
          dark: '#0b7268',
        },
      },
      fontFamily: {
        sans: [
          'Inter',
          'system-ui',
          '-apple-system',
          'Segoe UI',
          'Roboto',
          'Helvetica',
          'Arial',
          'sans-serif',
        ],
      },
      boxShadow: {
        card: '0 1px 2px rgba(16, 38, 61, 0.06), 0 4px 12px rgba(16, 38, 61, 0.06)',
      },
    },
  },
  plugins: [],
}

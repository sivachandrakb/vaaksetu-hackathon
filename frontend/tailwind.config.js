/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#e8f0fe',
          100: '#c5d6fc',
          500: '#1a56db',
          600: '#1648c8',
          700: '#1239a6',
          900: '#0a1f5c',
        },
        karnataka: '#E8232A', // Karnataka flag red
      }
    }
  },
  plugins: [],
}

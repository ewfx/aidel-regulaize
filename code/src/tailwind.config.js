/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './frontend/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        wf: {
          red: '#D71E28',
          gold: '#FFCD11',
          black: '#000000',
          gray: {
            DEFAULT: '#666666',
            light: '#F5F5F5',
            dark: '#333333'
          }
        }
      }
    },
  },
  plugins: [],
};
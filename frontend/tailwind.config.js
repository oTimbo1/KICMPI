/** @type {import('tailwindcss').Config} */
// KicMPi design tokens — see docs/KICMPI_STYLE_GUIDE.md §8
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        kicmpi: {
          blue: '#1668B1', // primary action / headings / links
          blueDeep: '#104D84', // hover (links)
          navy: '#0B3356', // hover (buttons) / dark hero
          magenta: '#E5027E', // accent: active, dates, CTA-on-white, highlights
          ink: '#333333', // primary text
          slate: '#4A4A4A', // secondary text
          muted: '#999999', // tertiary text
          line: '#E6E6E6', // hairlines
          stripeA: '#FCFCFC', // striped-section base
          stripeB: '#EBEBEB', // striped-section stripe
          dark: '#222222', // footer
          error: '#A51B00', // errors (Drupal palette red)
        },
      },
      fontFamily: {
        // Figtree = approved stand-in for the licensed Prometo (style guide §3)
        sans: ['Figtree', 'Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

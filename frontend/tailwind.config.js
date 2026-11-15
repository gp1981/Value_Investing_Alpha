/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        mono: ['"JetBrains Mono"', 'Courier New', 'monospace'],
      },
      colors: {
        terminal: {
          bg: '#0a0c10',
          panel: '#10141a',
          card: '#161b22',
          border: '#232936',
          borderLight: '#323b4d',
          green: '#00e676',
          amber: '#ffab00',
          cyan: '#00e5ff',
          red: '#ff5252',
          text: '#e6edf3',
          muted: '#7d8590',
        }
      }
    },
  },
  plugins: [],
}

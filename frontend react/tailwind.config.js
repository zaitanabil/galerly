/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        'science-blue': '#0066CC',
        'shark': '#1D1D1F',
        'light-gray': '#F5F5F7',
        'coral': {
          100: '#FFE5E2',
          200: '#FFB5AD',
          300: '#FF8A7F',
          DEFAULT: '#FF6F61',
        },
        'mint': '#98FF98',
      },
      fontFamily: {
        'sans': ['"Open Sauce Sans"', 'sans-serif'],
        'serif': ['"Open Sauce Sans"', 'sans-serif'],
        'outfit': ['"Open Sauce Sans"', 'sans-serif'],
        'playfair': ['"Open Sauce Sans"', 'sans-serif'],
      },
      borderRadius: {
        'xs': '10px',
        's': '12px',
        'm': '16px',
        'l': '20px',
        'xl': '28px',
      },
      spacing: {
        '18': '4.5rem',
        '112': '28rem',
        '128': '32rem',
      },
      boxShadow: {
        'glass': '0 8px 32px rgba(0, 0, 0, 0.15)',
        '3xl': '0 35px 60px -15px rgba(0, 0, 0, 0.3)',
      },
    },
  },
  plugins: [],
};

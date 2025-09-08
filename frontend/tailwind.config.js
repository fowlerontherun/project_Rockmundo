/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./pages/**/*.{html,js,jsx}', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        background: 'var(--bg-color)',
        text: 'var(--text-color)',
        accent: 'var(--accent-color)',
        border: 'var(--border-color)',
        surface: 'var(--surface-color)',
        muted: 'var(--muted-text)',
        success: 'var(--success-color)',
        error: 'var(--error-color)',
        inverseText: 'var(--inverse-text-color)',
      },
    },
  },
};

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./components/**/*.{js,vue,ts}",
    "./layouts/**/*.vue",
    "./pages/**/*.vue",
    "./plugins/**/*.{js,ts}",
    "./app.vue",
  ],
  theme: {
    colors: {
      // Remplace TOUTES les couleurs Tailwind par défaut
      transparent: 'transparent',
      current: 'currentColor',
      white: '#ffffff',
      black: '#000000',
        // Couleur principale : Jaune (#facc15)
        primary: {
          50: '#fefce8',
          100: '#fef9c3',
          200: '#fef08a',
          300: '#fde047',
          400: '#facc15',  // Jaune principal
          500: '#eab308',
          600: '#ca8a04',
          700: '#a16207',
          800: '#854d0e',
          900: '#713f12',
        },
        // Couleur secondaire : Noir (#1a1a1a)
        secondary: {
          50: '#f8f8f8',
          100: '#f0f0f0',
          200: '#e4e4e4',
          300: '#d1d1d1',
          400: '#b4b4b4',
          500: '#9a9a9a',
          600: '#818181',
          700: '#6a6a6a',
          800: '#5a5a5a',
          900: '#1a1a1a',  // Noir principal
          950: '#0a0a0a',
        },
        // Couleurs sémantiques basées sur la palette
        success: {
          50: '#fefce8',
          100: '#fef9c3',
          200: '#fef08a',
          300: '#fde047',
          400: '#facc15',  // Utilise le jaune pour succès
          500: '#eab308',
          600: '#ca8a04',
          700: '#a16207',
          800: '#854d0e',
          900: '#713f12',
        },
        warning: {
          50: '#fefce8',
          100: '#fef9c3',
          200: '#fef08a',
          300: '#fde047',
          400: '#facc15',  // Utilise le jaune pour avertissement
          500: '#eab308',
          600: '#ca8a04',
          700: '#a16207',
          800: '#854d0e',
          900: '#713f12',
        },
        danger: {
          50: '#f8f8f8',
          100: '#f0f0f0',
          200: '#e4e4e4',
          300: '#d1d1d1',
          400: '#b4b4b4',
          500: '#9a9a9a',
          600: '#818181',
          700: '#6a6a6a',
          800: '#5a5a5a',
          900: '#1a1a1a',  // Utilise le noir pour danger
        },
        info: {
          50: '#fefce8',
          100: '#fef9c3',
          200: '#fef08a',
          300: '#fde047',
          400: '#facc15',  // Utilise le jaune pour info
          500: '#eab308',
          600: '#ca8a04',
          700: '#a16207',
          800: '#854d0e',
          900: '#713f12',
        },
        // Garder gray pour les textes/bordures neutres
        gray: {
          50: '#f8f8f8',
          100: '#f0f0f0',
          200: '#e4e4e4',
          300: '#d1d1d1',
          400: '#b4b4b4',
          500: '#9a9a9a',
          600: '#818181',
          700: '#6a6a6a',
          800: '#5a5a5a',
          900: '#1a1a1a',
        },
      },
    extend: {
      colors: {
        // Couleurs des plateformes
        'platform-vinted': '#06b6d4',  // Cyan pour Vinted
        'platform-ebay': '#3b82f6',    // Blue pour eBay
        'platform-etsy': '#f97316',    // Orange pour Etsy
        'platform-facebook': '#1877f2', // Blue Facebook

        // Couleurs UI supplémentaires
        'ui-bg': '#f9fafb',
        'ui-bg-subtle': '#fafafa',
        'ui-border': '#f0f0f0',
        'ui-text-muted': '#6a6a6a',

        // Couleurs pour avatars/gradients
        pink: {
          400: '#f472b6',
          500: '#ec4899',
        },
        rose: {
          500: '#f43f5e',
        },
        blue: {
          400: '#60a5fa',
          500: '#3b82f6',
        },
        indigo: {
          500: '#6366f1',
        },
        orange: {
          400: '#fb923c',
          500: '#f97316',
        },
        amber: {
          500: '#f59e0b',
        },
        green: {
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
        },
      },
    },
  },
  safelist: [
    // Assure que les classes utilisées dynamiquement sont générées
    'bg-primary-50', 'bg-primary-100', 'bg-primary-400', 'bg-primary-500',
    'text-primary-400', 'text-primary-500', 'text-primary-600', 'text-primary-700',
    'bg-secondary-900', 'bg-secondary-800', 'bg-secondary-950',
    'text-secondary-900', 'text-secondary-700', 'text-secondary-600',
    'border-primary-400', 'border-gray-200', 'border-gray-300',
    'hover:bg-primary-500', 'hover:bg-secondary-800',
    // Couleurs plateformes
    'bg-platform-vinted', 'bg-platform-ebay', 'bg-platform-etsy', 'bg-platform-facebook',
    'text-platform-vinted', 'text-platform-ebay', 'text-platform-etsy', 'text-platform-facebook',
    // Couleurs UI
    'bg-ui-bg', 'bg-ui-bg-subtle', 'border-ui-border', 'text-ui-text-muted',
  ],
  plugins: [
    require('tailwindcss-primeui')
  ],
}

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
        // Couleurs sémantiques - Palette classique
        success: {
          50: '#ecfdf5',
          100: '#d1fae5',
          200: '#a7f3d0',
          300: '#6ee7b7',
          400: '#34d399',
          500: '#10b981',  // Vert principal
          600: '#059669',
          700: '#047857',
          800: '#065f46',
          900: '#064e3b',
        },
        warning: {
          50: '#fffbeb',
          100: '#fef3c7',
          200: '#fde68a',
          300: '#fcd34d',
          400: '#fbbf24',
          500: '#f59e0b',  // Orange principal
          600: '#d97706',
          700: '#b45309',
          800: '#92400e',
          900: '#78350f',
        },
        error: {
          50: '#fef2f2',
          100: '#fee2e2',
          200: '#fecaca',
          300: '#fca5a5',
          400: '#f87171',
          500: '#ef4444',  // Rouge principal
          600: '#dc2626',
          700: '#b91c1c',
          800: '#991b1b',
          900: '#7f1d1d',
        },
        danger: {
          50: '#fef2f2',
          100: '#fee2e2',
          200: '#fecaca',
          300: '#fca5a5',
          400: '#f87171',
          500: '#ef4444',  // Alias de error
          600: '#dc2626',
          700: '#b91c1c',
          800: '#991b1b',
          900: '#7f1d1d',
        },
        info: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',  // Bleu principal
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
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
    // Couleurs primaires et secondaires
    'bg-primary-50', 'bg-primary-100', 'bg-primary-400', 'bg-primary-500',
    'text-primary-400', 'text-primary-500', 'text-primary-600', 'text-primary-700',
    'bg-secondary-900', 'bg-secondary-800', 'bg-secondary-950',
    'text-secondary-900', 'text-secondary-700', 'text-secondary-600',
    'border-primary-400', 'border-gray-200', 'border-gray-300',
    'hover:bg-primary-500', 'hover:bg-secondary-800',
    // Couleurs sémantiques
    'bg-success-50', 'bg-success-100', 'bg-success-500', 'bg-success-600',
    'text-success-500', 'text-success-600', 'text-success-700', 'text-success-800',
    'bg-warning-50', 'bg-warning-100', 'bg-warning-500', 'bg-warning-600',
    'text-warning-500', 'text-warning-600', 'text-warning-700', 'text-warning-800',
    'bg-error-50', 'bg-error-100', 'bg-error-500', 'bg-error-600',
    'text-error-500', 'text-error-600', 'text-error-700', 'text-error-800',
    'bg-info-50', 'bg-info-100', 'bg-info-500', 'bg-info-600',
    'text-info-500', 'text-info-600', 'text-info-700', 'text-info-800',
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

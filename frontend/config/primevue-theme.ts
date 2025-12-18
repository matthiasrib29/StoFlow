import { definePreset } from '@primevue/themes'
import Lara from '@primevue/themes/lara'

/**
 * Stoflow Brand Color Palette
 *
 * Primary: Yellow (#facc15) - Represents energy, optimism, and visibility
 * Secondary: Black (#1a1a1a) - Provides contrast and professionalism
 *
 * This theme is applied across all PrimeVue components to maintain
 * brand consistency throughout the application.
 */

export const StoflowPreset = definePreset(Lara, {
  semantic: {
    primary: {
      50: '{yellow.50}',
      100: '{yellow.100}',
      200: '{yellow.200}',
      300: '{yellow.300}',
      400: '{yellow.400}',
      500: '{yellow.500}',
      600: '{yellow.600}',
      700: '{yellow.700}',
      800: '{yellow.800}',
      900: '{yellow.900}',
      950: '{yellow.950}'
    },
    colorScheme: {
      light: {
        primary: {
          color: '#facc15',         // Yellow 400
          inverseColor: '#1a1a1a',  // Near black
          hoverColor: '#eab308',    // Yellow 500 (darker)
          activeColor: '#ca8a04'    // Yellow 600 (even darker)
        },
        highlight: {
          background: '#facc15',
          focusBackground: '#eab308',
          color: '#1a1a1a',
          focusColor: '#1a1a1a'
        }
      }
    }
  }
})

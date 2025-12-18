import { defineNuxtPlugin } from '#app'
import PrimeVue from 'primevue/config'
import { definePreset } from '@primevue/themes'
import Lara from '@primevue/themes/lara'

// Core Components
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Card from 'primevue/card'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'

// Services
import Toast from 'primevue/toast'
import ToastService from 'primevue/toastservice'
import ConfirmDialog from 'primevue/confirmdialog'
import ConfirmationService from 'primevue/confirmationservice'
import Dialog from 'primevue/dialog'

// Form Components - PrimeVue v4
import Select from 'primevue/select'
import ToggleSwitch from 'primevue/toggleswitch'
import Checkbox from 'primevue/checkbox'
import Textarea from 'primevue/textarea'
import InputNumber from 'primevue/inputnumber'
import AutoComplete from 'primevue/autocomplete'
import SelectButton from 'primevue/selectbutton'

// Tabs - PrimeVue v4 (new structure)
import Tabs from 'primevue/tabs'
import TabList from 'primevue/tablist'
import Tab from 'primevue/tab'
import TabPanels from 'primevue/tabpanels'
import TabPanel from 'primevue/tabpanel'

// UI Components
import Badge from 'primevue/badge'
import ProgressBar from 'primevue/progressbar'
import ProgressSpinner from 'primevue/progressspinner'
import Divider from 'primevue/divider'
import Tree from 'primevue/tree'
import Message from 'primevue/message'
import Tag from 'primevue/tag'
import Tooltip from 'primevue/tooltip'

// Preset personnalisé Stoflow : Jaune (#facc15) & Noir (#1a1a1a)
const StoflowPreset = definePreset(Lara, {
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
          color: '#facc15',
          inverseColor: '#1a1a1a',
          hoverColor: '#eab308',
          activeColor: '#ca8a04'
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

export default defineNuxtPlugin((nuxtApp) => {
  nuxtApp.vueApp.use(PrimeVue, {
    ripple: true,
    theme: {
      preset: StoflowPreset,
      options: {
        darkModeSelector: '.dark-mode',
        cssLayer: false
      }
    }
  })

  // Services must be registered on client-side only (they depend on DOM)
  if (import.meta.client) {
    nuxtApp.vueApp.use(ToastService)
    nuxtApp.vueApp.use(ConfirmationService)
  }

  // Core Components
  nuxtApp.vueApp.component('Button', Button)
  nuxtApp.vueApp.component('InputText', InputText)
  nuxtApp.vueApp.component('Password', Password)
  nuxtApp.vueApp.component('Card', Card)
  nuxtApp.vueApp.component('DataTable', DataTable)
  nuxtApp.vueApp.component('Column', Column)
  nuxtApp.vueApp.component('Toast', Toast)
  nuxtApp.vueApp.component('ConfirmDialog', ConfirmDialog)
  nuxtApp.vueApp.component('Dialog', Dialog)

  // Form Components - PrimeVue v4
  nuxtApp.vueApp.component('Select', Select)
  nuxtApp.vueApp.component('ToggleSwitch', ToggleSwitch)
  nuxtApp.vueApp.component('Checkbox', Checkbox)
  nuxtApp.vueApp.component('Textarea', Textarea)
  nuxtApp.vueApp.component('InputNumber', InputNumber)
  nuxtApp.vueApp.component('AutoComplete', AutoComplete)
  nuxtApp.vueApp.component('SelectButton', SelectButton)

  // Tabs - PrimeVue v4
  nuxtApp.vueApp.component('Tabs', Tabs)
  nuxtApp.vueApp.component('TabList', TabList)
  nuxtApp.vueApp.component('Tab', Tab)
  nuxtApp.vueApp.component('TabPanels', TabPanels)
  nuxtApp.vueApp.component('TabPanel', TabPanel)

  // UI Components
  nuxtApp.vueApp.component('Badge', Badge)
  nuxtApp.vueApp.component('ProgressBar', ProgressBar)
  nuxtApp.vueApp.component('ProgressSpinner', ProgressSpinner)
  nuxtApp.vueApp.component('Divider', Divider)
  nuxtApp.vueApp.component('Tree', Tree)
  nuxtApp.vueApp.component('Message', Message)
  nuxtApp.vueApp.component('Tag', Tag)

  // Directives
  nuxtApp.vueApp.directive('tooltip', Tooltip)
})

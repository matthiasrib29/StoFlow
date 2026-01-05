/**
 * Composable for dashboard navigation state and menu toggles.
 * Handles sidebar menu state, mobile menu, and route-based menu opening.
 */

export function useDashboardNavigation() {
  const route = useRoute()

  // Mobile menu state
  const mobileMenuOpen = ref(false)

  // Main menu states
  const productsMenuOpen = ref(false)
  const platformsMenuOpen = ref(false)
  const subscriptionMenuOpen = ref(false)
  const settingsMenuOpen = ref(false)
  const adminMenuOpen = ref(false)

  // Platform submenu states
  const vintedMenuOpen = ref(false)
  const ebayMenuOpen = ref(false)
  const etsyMenuOpen = ref(false)

  // Route checks
  const isProductsRoute = computed(() => route.path.startsWith('/dashboard/products'))
  const isPlatformsRoute = computed(() => route.path.startsWith('/dashboard/platforms'))
  const isVintedRoute = computed(() => route.path.startsWith('/dashboard/platforms/vinted'))
  const isEbayRoute = computed(() => route.path.startsWith('/dashboard/platforms/ebay'))
  const isEtsyRoute = computed(() => route.path.startsWith('/dashboard/platforms/etsy'))
  const isSubscriptionRoute = computed(() => route.path.startsWith('/dashboard/subscription'))
  const isSettingsRoute = computed(() => route.path.startsWith('/dashboard/settings'))
  const isAdminRoute = computed(() => route.path.startsWith('/dashboard/admin'))

  // Toggle functions
  const toggleProductsMenu = () => { productsMenuOpen.value = !productsMenuOpen.value }
  const togglePlatformsMenu = () => { platformsMenuOpen.value = !platformsMenuOpen.value }
  const toggleSubscriptionMenu = () => { subscriptionMenuOpen.value = !subscriptionMenuOpen.value }
  const toggleSettingsMenu = () => { settingsMenuOpen.value = !settingsMenuOpen.value }
  const toggleAdminMenu = () => { adminMenuOpen.value = !adminMenuOpen.value }
  const toggleVintedMenu = () => { vintedMenuOpen.value = !vintedMenuOpen.value }
  const toggleEbayMenu = () => { ebayMenuOpen.value = !ebayMenuOpen.value }
  const toggleEtsyMenu = () => { etsyMenuOpen.value = !etsyMenuOpen.value }
  const closeMobileMenu = () => { mobileMenuOpen.value = false }
  const openMobileMenu = () => { mobileMenuOpen.value = true }

  // Auto-open menus based on current route
  const syncMenusWithRoute = (path: string) => {
    // Close mobile menu on navigation
    mobileMenuOpen.value = false

    // Open parent menus based on route
    if (path.startsWith('/dashboard/products')) {
      productsMenuOpen.value = true
    }
    if (path.startsWith('/dashboard/platforms')) {
      platformsMenuOpen.value = true
      if (path.startsWith('/dashboard/platforms/vinted')) {
        vintedMenuOpen.value = true
      }
      if (path.startsWith('/dashboard/platforms/ebay')) {
        ebayMenuOpen.value = true
      }
      if (path.startsWith('/dashboard/platforms/etsy')) {
        etsyMenuOpen.value = true
      }
    }
    if (path.startsWith('/dashboard/subscription')) {
      subscriptionMenuOpen.value = true
    }
    if (path.startsWith('/dashboard/settings')) {
      settingsMenuOpen.value = true
    }
    if (path.startsWith('/dashboard/admin')) {
      adminMenuOpen.value = true
    }
  }

  // Watch route changes
  watch(() => route.path, syncMenusWithRoute, { immediate: true })

  return {
    // Mobile menu
    mobileMenuOpen,
    openMobileMenu,
    closeMobileMenu,

    // Main menu states
    productsMenuOpen,
    platformsMenuOpen,
    subscriptionMenuOpen,
    settingsMenuOpen,
    adminMenuOpen,

    // Platform submenu states
    vintedMenuOpen,
    ebayMenuOpen,
    etsyMenuOpen,

    // Route checks
    isProductsRoute,
    isPlatformsRoute,
    isVintedRoute,
    isEbayRoute,
    isEtsyRoute,
    isSubscriptionRoute,
    isSettingsRoute,
    isAdminRoute,

    // Toggle functions
    toggleProductsMenu,
    togglePlatformsMenu,
    toggleSubscriptionMenu,
    toggleSettingsMenu,
    toggleAdminMenu,
    toggleVintedMenu,
    toggleEbayMenu,
    toggleEtsyMenu
  }
}

/**
 * Composable pour gérer les utilitaires des plateformes d'intégration
 */
export const usePlatform = () => {
  const getPlatformIcon = (platform: string): string => {
    const icons: Record<string, string> = {
      vinted: 'pi-shopping-bag',
      ebay: 'pi-shop',
      etsy: 'pi-heart',
      facebook: 'pi-facebook'
    }
    return icons[platform] || 'pi-link'
  }

  const getPlatformColor = (platform: string): { bg: string, text: string } => {
    const colors: Record<string, { bg: string, text: string }> = {
      vinted: { bg: 'bg-cyan-100', text: 'text-cyan-600' },
      ebay: { bg: 'bg-blue-100', text: 'text-blue-600' },
      etsy: { bg: 'bg-orange-100', text: 'text-orange-600' },
      facebook: { bg: 'bg-blue-100', text: 'text-blue-600' }
    }
    return colors[platform] || { bg: 'bg-gray-100', text: 'text-gray-600' }
  }

  return {
    getPlatformIcon,
    getPlatformColor
  }
}

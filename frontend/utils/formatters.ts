/**
 * Centralized formatting utilities for the frontend.
 * These functions were previously duplicated across 10+ files.
 */

/**
 * Formats a number as currency (EUR).
 *
 * @param value - The numeric value to format
 * @param currency - The currency code (default: 'EUR')
 * @param locale - The locale for formatting (default: 'fr-FR')
 * @returns Formatted currency string
 */
export function formatCurrency(
  value: number,
  currency: string = 'EUR',
  locale: string = 'fr-FR'
): string {
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency
  }).format(value)
}

/**
 * Formats a date string to a localized short date.
 *
 * @param dateStr - ISO date string or null
 * @param locale - The locale for formatting (default: 'fr-FR')
 * @returns Formatted date string (e.g., "5 janv. 2024") or '-' if invalid
 */
export function formatDate(
  dateStr: string | null | undefined,
  locale: string = 'fr-FR'
): string {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  if (isNaN(date.getTime())) return '-'
  return date.toLocaleDateString(locale, {
    day: 'numeric',
    month: 'short',
    year: 'numeric'
  })
}

/**
 * Formats a date string to a localized date with time.
 *
 * @param dateStr - ISO date string or null
 * @param locale - The locale for formatting (default: 'fr-FR')
 * @returns Formatted datetime string (e.g., "5 janv. 2024, 14:30") or '-' if invalid
 */
export function formatDateTime(
  dateStr: string | null | undefined,
  locale: string = 'fr-FR'
): string {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  if (isNaN(date.getTime())) return '-'
  return date.toLocaleString(locale, {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

/**
 * Product/listing status labels mapping.
 */
const STATUS_LABELS: Record<string, string> = {
  active: 'Actif',
  published: 'Publié',
  sold: 'Vendu',
  paused: 'En pause',
  expired: 'Expiré',
  pending: 'En attente',
  deleted: 'Supprimé',
  draft: 'Brouillon',
  archived: 'Archivé',
  reserved: 'Réservé',
  hidden: 'Masqué'
}

/**
 * Returns a human-readable label for a product/listing status.
 *
 * @param status - The status code
 * @returns Translated status label or the original status if not found
 */
export function getStatusLabel(status: string): string {
  return STATUS_LABELS[status] || status
}

/**
 * Status severity mapping for UI components (badges, tags).
 */
const STATUS_SEVERITIES: Record<string, string> = {
  active: 'success',
  published: 'success',
  sold: 'info',
  paused: 'warning',
  expired: 'danger',
  pending: 'secondary',
  deleted: 'danger',
  draft: 'secondary',
  archived: 'secondary',
  reserved: 'warning',
  hidden: 'secondary'
}

/**
 * Returns the severity level for a status (for UI styling).
 *
 * @param status - The status code
 * @returns Severity string (success, warning, danger, info, secondary)
 */
export function getStatusSeverity(status: string): string {
  return STATUS_SEVERITIES[status] || 'secondary'
}

/**
 * Formats a number with locale-specific separators.
 *
 * @param value - The numeric value to format
 * @param locale - The locale for formatting (default: 'fr-FR')
 * @returns Formatted number string
 */
export function formatNumber(value: number, locale: string = 'fr-FR'): string {
  return new Intl.NumberFormat(locale).format(value || 0)
}

/**
 * Formats a date string as relative time (e.g., "Il y a 5 min").
 *
 * @param dateStr - ISO date string
 * @returns Relative time string
 */
export function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)

  if (minutes < 1) return 'À l\'instant'
  if (minutes < 60) return `Il y a ${minutes} min`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `Il y a ${hours}h`
  const days = Math.floor(hours / 24)
  return `Il y a ${days}j`
}

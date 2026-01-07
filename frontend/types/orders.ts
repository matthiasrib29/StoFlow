/**
 * Order types for marketplace integrations
 */

export interface VintedOrder {
  transaction_id: string
  buyer_id: number
  buyer_login: string
  seller_id: number
  seller_login: string
  total_price: number
  shipping_price: number
  service_fee: number
  seller_revenue: number
  order_status: string
  shipping_status: string
  tracking_number?: string
  carrier?: string
  created_at_vinted: string
  shipped_at?: string
  delivered_at?: string
  completed_at?: string
  product_title: string
  product_photo?: string
  product_id?: number
  vinted_item_id?: number
  created_at: string
  updated_at: string
}

export interface EbayOrder {
  order_id: string
  marketplace_id?: string
  buyer_username: string
  buyer_email?: string
  total_price: number
  currency: string
  shipping_cost?: number
  order_payment_status: string
  order_fulfillment_status: string
  creation_date: string
  paid_date?: string
  tracking_number?: string
  shipping_carrier?: string
  shipping_name?: string
  shipping_address?: string
  shipping_city?: string
  shipping_postal_code?: string
  shipping_country?: string
  items_count: number
  created_at: string
  updated_at: string
}

export interface EbayOrderProduct {
  id: number
  order_id: string
  ebay_item_id: string
  product_id?: number
  title: string
  quantity: number
  price: number
  sku?: string
  line_item_id: string
}

export interface EtsyOrder {
  // Placeholder for future backend implementation
  receipt_id: string
  buyer_email: string
  total: number
  status: string
  created_timestamp: number
  shipped_timestamp?: number
}

/**
 * Order status helpers
 */
export const VintedOrderStatus = {
  PENDING: 'pending',
  PAID: 'paid',
  SHIPPED: 'shipped',
  DELIVERED: 'delivered',
  COMPLETED: 'completed',
  CANCELLED: 'cancelled'
} as const

export const EbayFulfillmentStatus = {
  NOT_STARTED: 'NOT_STARTED',
  IN_PROGRESS: 'IN_PROGRESS',
  FULFILLED: 'FULFILLED',
  CANCELLED: 'CANCELLED'
} as const

export const EbayPaymentStatus = {
  PAID: 'PAID',
  PENDING: 'PENDING',
  FAILED: 'FAILED'
} as const

/**
 * Filter types for orders
 */
export interface OrderFilters {
  search?: string
  status?: string
  dateFrom?: string
  dateTo?: string
}

/**
 * Stats types for orders dashboard
 */
export interface OrderStats {
  total_orders: number
  total_revenue: number
  pending_orders: number
  shipped_orders: number
  delivered_orders: number
  conversion_rate?: number
}

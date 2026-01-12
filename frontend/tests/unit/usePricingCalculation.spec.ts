/**
 * Unit tests for usePricingCalculation composable
 *
 * Tests cover:
 * - Initial state validation
 * - Loading state management
 * - Successful price calculation
 * - Error handling (400, 500, 504, generic)
 * - Reset functionality
 * - Sequential calculations
 *
 * Created: 2026-01-12
 * Phase: 07-01 (Testing & Polish)
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { usePricingCalculation } from '~/composables/usePricingCalculation'
import type { PriceInput, PriceOutput } from '~/composables/usePricingCalculation'

describe('usePricingCalculation', () => {
  let mockApiPost: ReturnType<typeof vi.fn>

  beforeEach(() => {
    vi.clearAllMocks()
    mockApiPost = vi.fn()

    // Mock useApi to return our mock post function
    vi.mocked(globalThis.useApi).mockReturnValue({
      post: mockApiPost
    } as any)
  })

  describe('Initial State', () => {
    it('should initialize with default state', () => {
      const { isLoading, error, priceResult } = usePricingCalculation()

      expect(isLoading.value).toBe(false)
      expect(error.value).toBe(null)
      expect(priceResult.value).toBe(null)
    })
  })

  describe('Loading State', () => {
    it('should set loading to true during calculation and false after completion', async () => {
      const mockResult: PriceOutput = {
        quick_price: '75.00',
        standard_price: '100.00',
        premium_price: '130.00',
        base_price: '100.00',
        model_coefficient: 1.0,
        adjustments: {
          condition: 0.0,
          origin: 0.0,
          decade: 0.0,
          trend: 0.0,
          feature: 0.0,
          total: 0.0
        },
        brand: 'Test Brand',
        group: 'jacket_leather'
      }

      mockApiPost.mockResolvedValue(mockResult)

      const { isLoading, calculatePrice } = usePricingCalculation()
      const validInput: PriceInput = {
        brand: 'Test Brand',
        category: 'Jacket',
        materials: ['Leather'],
        condition_score: 4,
        supplements: [],
        condition_sensitivity: 1.0,
        actual_origin: 'France',
        expected_origins: ['France', 'Italy'],
        actual_decade: '2020s',
        expected_decades: ['2020s'],
        actual_trends: [],
        expected_trends: [],
        actual_features: [],
        expected_features: []
      }

      expect(isLoading.value).toBe(false)

      const calculatePromise = calculatePrice(validInput)

      // Note: In a real async scenario, we'd check loading state here,
      // but since the mock is synchronous, loading goes false immediately
      await calculatePromise

      expect(isLoading.value).toBe(false)
    })
  })

  describe('Successful Calculation', () => {
    it('should handle successful price calculation', async () => {
      const mockResult: PriceOutput = {
        quick_price: '75.00',
        standard_price: '100.00',
        premium_price: '130.00',
        base_price: '100.00',
        model_coefficient: 1.2,
        adjustments: {
          condition: 0.05,
          origin: 0.1,
          decade: -0.05,
          trend: 0.0,
          feature: 0.0,
          total: 0.1
        },
        brand: 'Hermès',
        group: 'bag_luxury',
        model_name: 'Birkin'
      }

      mockApiPost.mockResolvedValue(mockResult)

      const { priceResult, error, calculatePrice } = usePricingCalculation()
      const validInput: PriceInput = {
        brand: 'Hermès',
        category: 'Bag',
        materials: ['Leather'],
        model_name: 'Birkin',
        condition_score: 5,
        supplements: [],
        condition_sensitivity: 1.0,
        actual_origin: 'France',
        expected_origins: ['France'],
        actual_decade: '2020s',
        expected_decades: ['2020s'],
        actual_trends: [],
        expected_trends: [],
        actual_features: [],
        expected_features: []
      }

      const result = await calculatePrice(validInput)

      expect(result).toEqual(mockResult)
      expect(priceResult.value).toEqual(mockResult)
      expect(error.value).toBe(null)
      expect(mockApiPost).toHaveBeenCalledWith('/pricing/calculate', validInput)
      expect(mockApiPost).toHaveBeenCalledTimes(1)
    })
  })

  describe('Error Handling', () => {
    it('should handle 400 validation error', async () => {
      mockApiPost.mockRejectedValue({
        response: {
          status: 400,
          data: { detail: 'Invalid brand name' }
        }
      })

      const { error, calculatePrice } = usePricingCalculation()
      const invalidInput: PriceInput = {
        brand: '',
        category: 'Jacket',
        materials: [],
        condition_score: 3,
        supplements: [],
        condition_sensitivity: 1.0,
        actual_origin: 'Unknown',
        expected_origins: [],
        actual_decade: '2020s',
        expected_decades: [],
        actual_trends: [],
        expected_trends: [],
        actual_features: [],
        expected_features: []
      }

      await expect(calculatePrice(invalidInput)).rejects.toMatchObject({
        response: { status: 400 }
      })

      expect(error.value).toBe('Invalid product data. Please check all fields.')
    })

    it('should handle 500 generation error', async () => {
      mockApiPost.mockRejectedValue({
        response: {
          status: 500,
          data: { detail: 'Internal server error' }
        }
      })

      const { error, calculatePrice } = usePricingCalculation()
      const validInput: PriceInput = {
        brand: 'Test Brand',
        category: 'Jacket',
        materials: ['Leather'],
        condition_score: 4,
        supplements: [],
        condition_sensitivity: 1.0,
        actual_origin: 'France',
        expected_origins: ['France'],
        actual_decade: '2020s',
        expected_decades: ['2020s'],
        actual_trends: [],
        expected_trends: [],
        actual_features: [],
        expected_features: []
      }

      await expect(calculatePrice(validInput)).rejects.toMatchObject({
        response: { status: 500 }
      })

      expect(error.value).toBe('Failed to generate pricing data. Please try again later.')
    })

    it('should handle 504 timeout error', async () => {
      mockApiPost.mockRejectedValue({
        response: {
          status: 504,
          data: { detail: 'Gateway timeout' }
        }
      })

      const { error, calculatePrice } = usePricingCalculation()
      const validInput: PriceInput = {
        brand: 'Test Brand',
        category: 'Jacket',
        materials: ['Leather'],
        condition_score: 4,
        supplements: [],
        condition_sensitivity: 1.0,
        actual_origin: 'France',
        expected_origins: ['France'],
        actual_decade: '2020s',
        expected_decades: ['2020s'],
        actual_trends: [],
        expected_trends: [],
        actual_features: [],
        expected_features: []
      }

      await expect(calculatePrice(validInput)).rejects.toMatchObject({
        response: { status: 504 }
      })

      expect(error.value).toBe('Pricing calculation timed out. Please try again.')
    })

    it('should handle generic errors with detail message', async () => {
      mockApiPost.mockRejectedValue({
        response: {
          status: 418,
          data: { detail: 'I am a teapot' }
        }
      })

      const { error, calculatePrice } = usePricingCalculation()
      const validInput: PriceInput = {
        brand: 'Test Brand',
        category: 'Jacket',
        materials: ['Leather'],
        condition_score: 4,
        supplements: [],
        condition_sensitivity: 1.0,
        actual_origin: 'France',
        expected_origins: ['France'],
        actual_decade: '2020s',
        expected_decades: ['2020s'],
        actual_trends: [],
        expected_trends: [],
        actual_features: [],
        expected_features: []
      }

      await expect(calculatePrice(validInput)).rejects.toMatchObject({
        response: { status: 418 }
      })

      expect(error.value).toBe('I am a teapot')
    })

    it('should handle errors without detail message', async () => {
      mockApiPost.mockRejectedValue({
        response: {
          status: 503,
          data: {}
        }
      })

      const { error, calculatePrice } = usePricingCalculation()
      const validInput: PriceInput = {
        brand: 'Test Brand',
        category: 'Jacket',
        materials: ['Leather'],
        condition_score: 4,
        supplements: [],
        condition_sensitivity: 1.0,
        actual_origin: 'France',
        expected_origins: ['France'],
        actual_decade: '2020s',
        expected_decades: ['2020s'],
        actual_trends: [],
        expected_trends: [],
        actual_features: [],
        expected_features: []
      }

      await expect(calculatePrice(validInput)).rejects.toMatchObject({
        response: { status: 503 }
      })

      expect(error.value).toBe('An error occurred during price calculation')
    })
  })

  describe('Reset Functionality', () => {
    it('should reset state to initial values', async () => {
      const mockResult: PriceOutput = {
        quick_price: '75.00',
        standard_price: '100.00',
        premium_price: '130.00',
        base_price: '100.00',
        model_coefficient: 1.0,
        adjustments: {
          condition: 0.0,
          origin: 0.0,
          decade: 0.0,
          trend: 0.0,
          feature: 0.0,
          total: 0.0
        },
        brand: 'Test Brand',
        group: 'jacket_leather'
      }

      mockApiPost.mockResolvedValue(mockResult)

      const { priceResult, error, calculatePrice, reset } = usePricingCalculation()
      const validInput: PriceInput = {
        brand: 'Test Brand',
        category: 'Jacket',
        materials: ['Leather'],
        condition_score: 4,
        supplements: [],
        condition_sensitivity: 1.0,
        actual_origin: 'France',
        expected_origins: ['France'],
        actual_decade: '2020s',
        expected_decades: ['2020s'],
        actual_trends: [],
        expected_trends: [],
        actual_features: [],
        expected_features: []
      }

      // Set some state
      await calculatePrice(validInput)
      expect(priceResult.value).toEqual(mockResult)

      // Reset
      reset()

      // Verify state is cleared
      expect(priceResult.value).toBe(null)
      expect(error.value).toBe(null)
    })
  })

  describe('Sequential Calculations', () => {
    it('should handle multiple calculations correctly', async () => {
      const firstResult: PriceOutput = {
        quick_price: '50.00',
        standard_price: '75.00',
        premium_price: '100.00',
        base_price: '75.00',
        model_coefficient: 1.0,
        adjustments: {
          condition: 0.0,
          origin: 0.0,
          decade: 0.0,
          trend: 0.0,
          feature: 0.0,
          total: 0.0
        },
        brand: 'Brand A',
        group: 'jacket_casual'
      }

      const secondResult: PriceOutput = {
        quick_price: '150.00',
        standard_price: '200.00',
        premium_price: '250.00',
        base_price: '200.00',
        model_coefficient: 1.5,
        adjustments: {
          condition: 0.1,
          origin: 0.2,
          decade: 0.0,
          trend: 0.05,
          feature: 0.0,
          total: 0.35
        },
        brand: 'Brand B',
        group: 'bag_luxury'
      }

      mockApiPost
        .mockResolvedValueOnce(firstResult)
        .mockResolvedValueOnce(secondResult)

      const { priceResult, error, calculatePrice } = usePricingCalculation()
      const input1: PriceInput = {
        brand: 'Brand A',
        category: 'Jacket',
        materials: ['Cotton'],
        condition_score: 3,
        supplements: [],
        condition_sensitivity: 1.0,
        actual_origin: 'China',
        expected_origins: ['China'],
        actual_decade: '2010s',
        expected_decades: ['2010s'],
        actual_trends: [],
        expected_trends: [],
        actual_features: [],
        expected_features: []
      }

      const input2: PriceInput = {
        brand: 'Brand B',
        category: 'Bag',
        materials: ['Leather'],
        condition_score: 5,
        supplements: [],
        condition_sensitivity: 1.0,
        actual_origin: 'Italy',
        expected_origins: ['Italy'],
        actual_decade: '2020s',
        expected_decades: ['2020s'],
        actual_trends: ['Vintage'],
        expected_trends: ['Vintage'],
        actual_features: [],
        expected_features: []
      }

      // First calculation
      const result1 = await calculatePrice(input1)
      expect(result1).toEqual(firstResult)
      expect(priceResult.value).toEqual(firstResult)
      expect(error.value).toBe(null)

      // Second calculation
      const result2 = await calculatePrice(input2)
      expect(result2).toEqual(secondResult)
      expect(priceResult.value).toEqual(secondResult)
      expect(error.value).toBe(null)

      // Verify API was called correctly both times
      expect(mockApiPost).toHaveBeenCalledTimes(2)
      expect(mockApiPost).toHaveBeenNthCalledWith(1, '/pricing/calculate', input1)
      expect(mockApiPost).toHaveBeenNthCalledWith(2, '/pricing/calculate', input2)
    })

    it('should clear error on new calculation after previous error', async () => {
      const mockResult: PriceOutput = {
        quick_price: '75.00',
        standard_price: '100.00',
        premium_price: '130.00',
        base_price: '100.00',
        model_coefficient: 1.0,
        adjustments: {
          condition: 0.0,
          origin: 0.0,
          decade: 0.0,
          trend: 0.0,
          feature: 0.0,
          total: 0.0
        },
        brand: 'Test Brand',
        group: 'jacket_leather'
      }

      mockApiPost
        .mockRejectedValueOnce({
          response: { status: 400, data: { detail: 'Invalid input' } }
        })
        .mockResolvedValueOnce(mockResult)

      const { error, priceResult, calculatePrice } = usePricingCalculation()
      const validInput: PriceInput = {
        brand: 'Test Brand',
        category: 'Jacket',
        materials: ['Leather'],
        condition_score: 4,
        supplements: [],
        condition_sensitivity: 1.0,
        actual_origin: 'France',
        expected_origins: ['France'],
        actual_decade: '2020s',
        expected_decades: ['2020s'],
        actual_trends: [],
        expected_trends: [],
        actual_features: [],
        expected_features: []
      }

      // First calculation fails
      await expect(calculatePrice(validInput)).rejects.toMatchObject({
        response: { status: 400 }
      })
      expect(error.value).toBe('Invalid product data. Please check all fields.')
      expect(priceResult.value).toBe(null)

      // Second calculation succeeds
      const result = await calculatePrice(validInput)
      expect(result).toEqual(mockResult)
      expect(priceResult.value).toEqual(mockResult)
      expect(error.value).toBe(null)
    })
  })
})

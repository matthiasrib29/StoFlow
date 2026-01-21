/**
 * Settings Schema with Zod Validation
 *
 * SECURITY: Validates all settings loaded from chrome.storage.local
 * to prevent injection of malicious or invalid configuration values.
 *
 * Author: Claude
 * Date: 2026-01-21
 */

import { z } from 'zod';

// ============================================================
// PLATFORM SCHEMA
// ============================================================

const PlatformConfigSchema = z.object({
  enabled: z.boolean().default(false),
  autoImport: z.boolean().default(false)
});

// ============================================================
// MAIN SETTINGS SCHEMA
// ============================================================

export const SettingsSchema = z.object({
  syncInterval: z
    .number()
    .min(30, 'Minimum 30 seconds')
    .max(3600, 'Maximum 1 hour')
    .default(60),
  autoSync: z.boolean().default(true),
  notifications: z.boolean().default(true),
  platforms: z
    .object({
      vinted: PlatformConfigSchema.default({ enabled: true, autoImport: false }),
      ebay: PlatformConfigSchema.default({ enabled: true, autoImport: false }),
      etsy: PlatformConfigSchema.default({ enabled: false, autoImport: false })
    })
    .default({})
});

// ============================================================
// TYPES
// ============================================================

export type PlatformConfig = z.infer<typeof PlatformConfigSchema>;
export type Settings = z.infer<typeof SettingsSchema>;

// ============================================================
// DEFAULT VALUES
// ============================================================

export const DEFAULT_SETTINGS: Settings = {
  syncInterval: 60,
  autoSync: true,
  notifications: true,
  platforms: {
    vinted: { enabled: true, autoImport: false },
    ebay: { enabled: true, autoImport: false },
    etsy: { enabled: false, autoImport: false }
  }
};

// ============================================================
// SAFE LOAD/SAVE FUNCTIONS
// ============================================================

/**
 * Safely load settings from chrome.storage.local with validation.
 * Returns validated settings or defaults on validation failure.
 */
export async function loadSettingsSafe(): Promise<Settings> {
  try {
    const stored = await chrome.storage.local.get('settings');

    if (!stored.settings) {
      console.debug('[Settings] No stored settings, using defaults');
      return DEFAULT_SETTINGS;
    }

    // Validate and coerce to correct types
    const result = SettingsSchema.safeParse(stored.settings);

    if (result.success) {
      console.debug('[Settings] Loaded and validated settings');
      return result.data;
    } else {
      console.warn('[Settings] Invalid stored settings, using defaults:', result.error.errors);
      return DEFAULT_SETTINGS;
    }
  } catch (error) {
    console.error('[Settings] Error loading settings:', error);
    return DEFAULT_SETTINGS;
  }
}

/**
 * Safely save settings to chrome.storage.local with validation.
 * Throws an error if settings are invalid.
 */
export async function saveSettingsSafe(settings: Settings): Promise<void> {
  // Validate before saving
  const result = SettingsSchema.safeParse(settings);

  if (!result.success) {
    const errors = result.error.errors.map((e) => `${e.path.join('.')}: ${e.message}`).join(', ');
    throw new Error(`Invalid settings: ${errors}`);
  }

  await chrome.storage.local.set({ settings: result.data });
  console.debug('[Settings] Settings saved successfully');
}

/**
 * Validate settings without saving.
 * Returns validation result with errors if invalid.
 */
export function validateSettings(settings: unknown): {
  valid: boolean;
  data?: Settings;
  errors?: string[];
} {
  const result = SettingsSchema.safeParse(settings);

  if (result.success) {
    return { valid: true, data: result.data };
  }

  return {
    valid: false,
    errors: result.error.errors.map((e) => `${e.path.join('.')}: ${e.message}`)
  };
}

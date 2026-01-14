# StoFlow Design Skill

| name | description |
|------|-------------|
| stoflow-design | Create frontend components following StoFlow's design system. Use this skill when building UI for the StoFlow e-commerce management platform. Generates consistent, on-brand components with proper fonts, colors, and animations. |

## Overview

StoFlow is a multi-marketplace e-commerce management platform (Vinted, eBay, Etsy). This skill ensures all generated frontend code follows the established design system.

## Brand Identity

**Tone**: Professional but modern, not corporate. Premium SaaS feel.
**Target Users**: E-commerce sellers (semi-pro to professional)
**Content Type**: Data-heavy dashboards, product management, marketplace integrations

## Typography System

| Usage | Font | Tailwind Class |
|-------|------|----------------|
| Headings | Plus Jakarta Sans | `font-display` |
| Body text | IBM Plex Sans | `font-body` or `font-sans` (default) |
| Code/SKUs | JetBrains Mono | `font-mono` |

### Rules
- All h1-h6 automatically use `font-display`
- Body text defaults to `font-body` (IBM Plex Sans)
- Use `font-mono` or `.sku` / `.reference` classes for product codes
- Headings use `tracking-tight` for tighter letter-spacing
- Weight: 600-800 for titles, 400-500 for body

## Color Palette

### Primary Colors
```
Primary (Yellow/Gold):
- primary-400: #facc15 (main)
- primary-500: #eab308 (hover)
- primary-50 to primary-900 scale available

Secondary (Black):
- secondary-900: #1a1a1a (main)
- secondary-950: #0a0a0a (darker)
```

### Semantic Colors
```
Success: success-500 (#10b981) - green
Warning: warning-500 (#f59e0b) - orange
Error: error-500 (#ef4444) - red
Info: info-500 (#3b82f6) - blue
```

### Platform Colors
```
Vinted: platform-vinted (#06b6d4) - cyan
eBay: platform-ebay (#3b82f6) - blue
Etsy: platform-etsy (#f97316) - orange
Facebook: platform-facebook (#1877f2) - blue
```

## Available Component Classes

### Buttons
```html
<!-- Primary (gold) -->
<button class="btn-primary">Action</button>

<!-- Secondary (gray) -->
<button class="btn-secondary">Cancel</button>

<!-- Danger -->
<button class="btn-danger">Delete</button>
<button class="btn-danger-solid">Delete</button>

<!-- Success -->
<button class="btn-success">Confirm</button>
<button class="btn-success-solid">Confirm</button>

<!-- Outline variants -->
<button class="btn-outline">Outline</button>
<button class="btn-outline-primary">Primary Outline</button>

<!-- Ghost -->
<button class="btn-ghost">Ghost</button>

<!-- Sizes -->
<button class="btn-primary btn-sm">Small</button>
<button class="btn-primary btn-lg">Large</button>
```

### Cards
```html
<!-- Standard card with hover -->
<div class="card">...</div>

<!-- Static card (no hover) -->
<div class="card-static">...</div>

<!-- Stat card for dashboards -->
<div class="stat-card">...</div>

<!-- Card with sections -->
<div class="card">
  <div class="card-header">Header</div>
  <div class="card-body">Content</div>
  <div class="card-footer">Footer</div>
</div>
```

### Badges
```html
<span class="badge badge-success">Active</span>
<span class="badge badge-warning">Pending</span>
<span class="badge badge-error">Error</span>
<span class="badge badge-info">Info</span>
<span class="badge badge-neutral">Draft</span>
<span class="badge badge-primary">Featured</span>
```

### Platform Badges
```html
<!-- Monochrome container + colored icon -->
<div class="platform-badge">
  <i class="pi pi-shopping-cart platform-icon-vinted"></i>
  Vinted
</div>
```

### Alerts
```html
<div class="alert alert-success">Success message</div>
<div class="alert alert-warning">Warning message</div>
<div class="alert alert-error">Error message</div>
<div class="alert alert-info">Info message</div>
```

### Typography
```html
<h1 class="page-title">Page Title</h1>
<p class="page-subtitle">Subtitle text</p>

<h2 class="section-title">Section Title</h2>
<h3 class="card-title">Card Title</h3>

<span class="text-muted">Muted text</span>
<span class="sku">SKU-2026-0142</span>
```

### Layout
```html
<div class="page-container">
  <div class="page-header">
    <h1 class="page-title">Dashboard</h1>
    <button class="btn-primary">Action</button>
  </div>

  <!-- Stats grid (4 columns) -->
  <div class="stats-grid">...</div>

  <!-- Cards grid (3 columns) -->
  <div class="cards-grid">...</div>
</div>
```

### Empty States
```html
<div class="empty-state">
  <i class="pi pi-inbox empty-state-icon"></i>
  <h3 class="empty-state-title">No products yet</h3>
  <p class="empty-state-description">Add your first product to get started</p>
  <button class="btn-primary">Add Product</button>
</div>
```

## Animations

### Stagger Grid (entry animations)
```html
<!-- Fade-in-up with stagger delay -->
<div class="stats-grid stagger-grid">
  <div class="stat-card">...</div>
  <div class="stat-card">...</div>
</div>

<!-- Faster variant -->
<div class="cards-grid stagger-grid-fast">...</div>

<!-- Scale variant -->
<div class="stagger-grid-scale">...</div>
```

### Micro-interactions
```html
<!-- Hover lift -->
<div class="hover-lift">Lifts on hover</div>
<div class="hover-lift-smooth">Smooth lift</div>

<!-- Hover glow (gold) -->
<div class="hover-glow">Glows on hover</div>

<!-- Button press -->
<button class="btn-press">Press effect</button>
```

### Utility Animations
```html
<div class="fade-in">Fades in on mount</div>
<div class="slide-in-right">Slides from right</div>
<div class="float">Floating animation</div>
<div class="spinner">Rotating spinner</div>
```

## PrimeVue Integration

StoFlow uses PrimeVue components with custom styling. The design system overrides PrimeVue defaults:

- Cards: 16px border-radius, subtle shadows
- Buttons: 12px border-radius, 600 font-weight
- Inputs: 12px border-radius, gold focus ring
- Tables: Modern headers, hover highlighting
- Dialogs: 20px border-radius, larger shadows

**Focus color**: Always use primary-400 (#facc15) for focus rings.

## Implementation Guidelines

1. **Always use existing classes** from design-system.css before creating custom styles
2. **Platform differentiation**: Use platform colors only for icons/accents, not backgrounds
3. **Consistency**: Stats use `stat-card`, content uses `card`
4. **Animations**: Use `stagger-grid` for grid entrances, `hover-lift` for interactive cards
5. **Typography**: Let headings auto-apply `font-display`, don't override
6. **Spacing**: Use `page-container` for page padding, consistent gap-4 or gap-6 for grids

## CSS Variables (Design Tokens)

All design tokens are centralized in `design-tokens.css`. Use CSS variables for custom styling:

### Colors
```css
/* Primary */
var(--color-primary-400)   /* Main gold: #facc15 */
var(--color-primary-500)   /* Hover: #eab308 */

/* Secondary */
var(--color-secondary-900) /* Main black: #1a1a1a */

/* Semantic */
var(--color-success-500)   /* Green: #10b981 */
var(--color-warning-500)   /* Orange: #f59e0b */
var(--color-error-500)     /* Red: #ef4444 */
var(--color-info-500)      /* Blue: #3b82f6 */

/* Platforms */
var(--color-platform-vinted)   /* Cyan */
var(--color-platform-ebay)     /* Blue */
var(--color-platform-etsy)     /* Orange */
```

### Typography
```css
var(--font-display)  /* Plus Jakarta Sans */
var(--font-body)     /* IBM Plex Sans */
var(--font-mono)     /* JetBrains Mono */
```

### Spacing & Radius
```css
/* Spacing */
var(--space-4)   /* 1rem / 16px */
var(--space-6)   /* 1.5rem / 24px */

/* Border radius */
var(--radius-button)  /* 12px */
var(--radius-card)    /* 16px */
var(--radius-dialog)  /* 20px */
```

### Shadows
```css
var(--shadow-card)        /* Subtle card shadow */
var(--shadow-card-hover)  /* Card hover state */
var(--shadow-dialog)      /* Modal shadow */
var(--shadow-focus-primary)  /* Gold focus ring */
```

### Transitions
```css
var(--transition-fast)    /* 150ms */
var(--transition-normal)  /* 200ms */
var(--transition-slow)    /* 300ms */
```

### Gradients
```css
var(--gradient-primary)   /* Gold gradient */
var(--gradient-vinted)    /* Vinted cyan */
var(--gradient-ebay)      /* eBay blue */
var(--gradient-etsy)      /* Etsy orange */
```

## What NOT to Do

- Don't use Inter, Roboto, or system fonts
- Don't create purple gradients
- Don't use generic gray backgrounds (#f5f5f5) - use `bg-ui-bg` or `bg-gray-50`
- Don't create new button styles - use btn-* classes
- Don't override PrimeVue with !important unless necessary
- Don't use scattered micro-interactions - prefer one orchestrated page load animation

# Chrome Web Store Listing - Stoflow Extension

This document contains the content for the Chrome Web Store listing.

---

## Extension Name

**Stoflow - Multi-Marketplace Manager**

---

## Short Description (132 characters max)

Manage your Vinted, eBay, and Etsy listings from one place. Import, publish, and sync products across marketplaces effortlessly.

---

## Detailed Description

**Stoflow** is the ultimate tool for e-commerce sellers who manage inventory across multiple marketplaces.

### Key Features

**Import Products**
- Import your existing Vinted wardrobe to Stoflow
- Bulk import support for large inventories
- Automatic data mapping

**Publish Anywhere**
- Publish products to Vinted directly from Stoflow
- Update listings across all platforms simultaneously
- Manage pricing and inventory in one place

**Sync Automatically**
- Keep your inventory synchronized
- Automatic status updates when items sell
- Real-time sync between platforms

**Time-Saving Dashboard**
- Manage all your products from stoflow.io
- Filter, search, and organize your inventory
- Track sales and performance

### How It Works

1. Install the Stoflow extension
2. Open www.vinted.fr in a browser tab
3. Navigate to stoflow.io
4. Connect your Vinted account
5. Start managing your products!

### Supported Marketplaces

- Vinted (France, Belgium, Netherlands, Germany, and more)
- eBay (coming soon)
- Etsy (coming soon)

### Why Choose Stoflow?

- **Save Time**: Manage all platforms from one dashboard
- **No Fees**: Free extension, optional premium features
- **Secure**: Your credentials never leave your browser
- **Privacy First**: We don't sell your data

### Requirements

- A Vinted account
- A Stoflow account (free registration at stoflow.io)
- Chrome, Edge, or Firefox browser

### Support

Need help? Visit our support page at https://stoflow.io/support or email us at support@stoflow.io

---

## Category

**Shopping**

---

## Language

**French** (primary)
**English** (secondary)

---

## Screenshots

1. **Dashboard Overview** - Show the main Stoflow dashboard with products
2. **Import from Vinted** - Show the import process
3. **Product Management** - Show editing a product
4. **Multi-Platform Sync** - Show sync status across platforms
5. **Extension Popup** - Show the extension popup interface

---

## Promotional Images

### Small Tile (440x280)
- Stoflow logo with tagline "Manage all your marketplaces"

### Large Tile (920x680)
- Feature showcase with screenshots

### Marquee (1400x560)
- Hero image with key features highlighted

---

## Privacy Practices

### Single Purpose Description

This extension connects stoflow.io with Vinted to enable product management and synchronization between the two platforms.

### Permission Justifications

| Permission | Justification |
|------------|---------------|
| `storage` | Store user preferences and session tokens locally |
| `tabs` | Detect open Vinted tabs to execute API calls |
| `activeTab` | Access the current Vinted tab to perform user-requested actions |
| `scripting` | Inject content scripts into Vinted pages for API access |
| `notifications` | Show sync status and important updates |
| `host_permissions (vinted.fr)` | Execute Vinted API calls with user's session |
| `host_permissions (stoflow.io)` | Communicate between extension and Stoflow dashboard |

### Data Usage

- **User data collected**: Vinted user ID, product listings, transaction history
- **User data NOT collected**: Passwords, payment info, browsing history
- **Data transmission**: Encrypted (HTTPS) to Stoflow servers for sync
- **Data sharing**: Not sold or shared with third parties
- **Data retention**: Until user requests deletion

---

## Contact Information

**Developer Name:** Stoflow SAS
**Email:** contact@stoflow.io
**Website:** https://stoflow.io
**Privacy Policy:** https://stoflow.io/privacy
**Terms of Service:** https://stoflow.io/terms

---

## Version History

### v2.0.0 (Current)
- Complete rewrite with Manifest V3
- New externally_connectable architecture
- Improved security and performance
- Firefox support via postMessage fallback

### v1.x (Legacy)
- Initial release with basic Vinted integration

---

## Review Notes for Google

This extension is designed for e-commerce sellers who use Vinted to sell second-hand items. It allows them to manage their Vinted inventory through the Stoflow web application (stoflow.io).

**How to test:**
1. Install the extension
2. Create a free account at stoflow.io
3. Open www.vinted.fr and log in
4. Go to stoflow.io and connect your Vinted account
5. Try importing products from Vinted

**Security measures:**
- All API calls are validated against an endpoint whitelist
- Origins are validated against a strict whitelist
- No remote code execution
- All data encrypted in transit

---

*Last updated: January 19, 2026*

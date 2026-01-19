# Manifest Configuration

The Farcaster manifest is served at `/.well-known/farcaster.json`. In Next.js, this is a route handler.

## Route Location

```
app/
└── .well-known/
    └── farcaster.json/
        └── route.ts
```

## Before (MiniKit)

MiniKit typically generates this from environment variables and OnchainKit config:

```typescript
// app/.well-known/farcaster.json/route.ts (MiniKit version)
export async function GET() {
  return Response.json({
    accountAssociation: {
      header: process.env.FARCASTER_HEADER,
      payload: process.env.FARCASTER_PAYLOAD,
      signature: process.env.FARCASTER_SIGNATURE,
    },
    frame: {
      version: "1",
      name: process.env.NEXT_PUBLIC_ONCHAINKIT_PROJECT_NAME,
      iconUrl: process.env.NEXT_PUBLIC_ICON_URL,
      splashImageUrl: process.env.NEXT_PUBLIC_SPLASH_IMAGE,
      splashBackgroundColor: process.env.NEXT_PUBLIC_SPLASH_BACKGROUND_COLOR,
      homeUrl: process.env.NEXT_PUBLIC_URL,
      webhookUrl: `${process.env.NEXT_PUBLIC_URL}/api/webhook`,
    },
  });
}
```

## After (Farcaster SDK)

The Farcaster SDK uses the `miniapp` key instead of `frame`:

```typescript
// app/.well-known/farcaster.json/route.ts
export async function GET() {
  const appUrl = process.env.NEXT_PUBLIC_URL;

  return Response.json({
    accountAssociation: {
      header: process.env.FARCASTER_HEADER,
      payload: process.env.FARCASTER_PAYLOAD,
      signature: process.env.FARCASTER_SIGNATURE,
    },
    miniapp: {
      version: "1",
      name: process.env.NEXT_PUBLIC_APP_NAME,
      homeUrl: appUrl,
      iconUrl: `${appUrl}/icon.png`,
      splashImageUrl: `${appUrl}/splash.png`,
      splashBackgroundColor: process.env.NEXT_PUBLIC_SPLASH_BACKGROUND_COLOR || "#000000",
      
      // Optional metadata
      subtitle: process.env.NEXT_PUBLIC_APP_SUBTITLE,
      description: process.env.NEXT_PUBLIC_APP_DESCRIPTION,
      screenshotUrls: [
        `${appUrl}/screenshots/1.png`,
        `${appUrl}/screenshots/2.png`,
      ],
      primaryCategory: process.env.NEXT_PUBLIC_APP_CATEGORY || "utilities",
      tags: ["farcaster"],
      
      // Open Graph
      heroImageUrl: `${appUrl}/hero.png`,
      tagline: process.env.NEXT_PUBLIC_APP_TAGLINE,
      ogTitle: process.env.NEXT_PUBLIC_APP_NAME,
      ogDescription: process.env.NEXT_PUBLIC_APP_DESCRIPTION,
      ogImageUrl: `${appUrl}/og.png`,
      
      // Webhook for notifications
      webhookUrl: `${appUrl}/api/webhook`,
      
      // Set to true to hide from search/discovery
      noindex: false,
    },
  });
}
```

## Full Manifest Schema

```typescript
interface FarcasterManifest {
  accountAssociation: {
    header: string;    // Base64 encoded JSON with fid, type, key
    payload: string;   // Base64 encoded JSON with domain
    signature: string; // Hex signature
  };
  miniapp: {
    // Required
    version: "1";
    name: string;              // App name (max 32 chars)
    homeUrl: string;           // Main app URL
    iconUrl: string;           // App icon (1:1 ratio, min 200x200)
    splashImageUrl: string;    // Splash screen image (1:1 ratio)
    splashBackgroundColor: string; // Hex color (e.g., "#000000")

    // Recommended
    subtitle?: string;         // Short tagline (max 64 chars)
    description?: string;      // Full description (max 256 chars)
    screenshotUrls?: string[]; // Screenshots (3:2 ratio, max 5)
    primaryCategory?: MiniAppCategory;
    tags?: string[];           // Keywords for discovery

    // Open Graph (for social sharing)
    heroImageUrl?: string;     // 3:2 ratio hero image
    tagline?: string;          // Short tagline for OG
    ogTitle?: string;          // OG title
    ogDescription?: string;    // OG description
    ogImageUrl?: string;       // OG image (1200x630)

    // Functionality
    webhookUrl?: string;       // For notifications and events
    
    // Discovery
    noindex?: boolean;         // Hide from search (default: false)
  };
}

type MiniAppCategory = 
  | "games"
  | "social" 
  | "finance"
  | "utilities"
  | "productivity"
  | "entertainment"
  | "news"
  | "shopping"
  | "health"
  | "education";
```

## Key Differences: MiniKit vs Farcaster SDK

| Field | MiniKit (`frame`) | Farcaster SDK (`miniapp`) |
|-------|-------------------|---------------------------|
| Root key | `frame` | `miniapp` |
| Subtitle | Not supported | `subtitle` |
| Description | Not standard | `description` |
| Screenshots | Not standard | `screenshotUrls` |
| Category | `primaryCategory` | `primaryCategory` |
| Hero image | Not standard | `heroImageUrl` |
| Tagline | Not standard | `tagline` |
| OG fields | Not standard | `ogTitle`, `ogDescription`, `ogImageUrl` |
| No index | Not standard | `noindex` |

## Environment Variables

Update your `.env` file:

```env
# App Identity
NEXT_PUBLIC_URL=https://yourapp.com
NEXT_PUBLIC_APP_NAME=My Mini App
NEXT_PUBLIC_APP_SUBTITLE=Do cool things
NEXT_PUBLIC_APP_DESCRIPTION=A longer description of what your app does
NEXT_PUBLIC_APP_CATEGORY=utilities
NEXT_PUBLIC_APP_TAGLINE=The best app ever
NEXT_PUBLIC_SPLASH_BACKGROUND_COLOR=#1a1a2e

# Farcaster Account Association (from manifest signing)
FARCASTER_HEADER=eyJmaWQi...
FARCASTER_PAYLOAD=eyJkb21h...
FARCASTER_SIGNATURE=MHgxMGQw...
```

## Generating Account Association

The `accountAssociation` proves you own the domain. Generate it using:

1. Go to [Farcaster Developer Tools](https://warpcast.com/~/developers/new)
2. Or use the Warpcast Farcaster JSON Tool
3. Connect your Farcaster custody wallet
4. Sign for your domain
5. Copy the `header`, `payload`, and `signature`

## Example Complete Manifest

```json
{
  "accountAssociation": {
    "header": "eyJmaWQiOjkxNTIsInR5cGUiOiJjdXN0b2R5Iiwia2V5IjoiMHgwMmVmNzkwRGQ3OTkzQTM1ZkQ4NDdDMDUzRURkQUU5NDBEMDU1NTk2In0",
    "payload": "eyJkb21haW4iOiJhcHAuZXhhbXBsZS5jb20ifQ",
    "signature": "MHgxMGQwZGU4ZGYwZDUwZTdmMGIxN2YxMTU2NDI1MjRmZTY0MTUyZGU4ZGU1MWU0MThiYjU4ZjVmZmQxYjRjNDBiNGVlZTRhNDcwNmVmNjhlMzQ0ZGQ5MDBkYmQyMmNlMmVlZGY5ZGQ0N2JlNWRmNzMwYzUxNjE4OWVjZDJjY2Y0MDFj"
  },
  "miniapp": {
    "version": "1",
    "name": "Crypto Portfolio Tracker",
    "homeUrl": "https://ex.co",
    "iconUrl": "https://ex.co/i.png",
    "splashImageUrl": "https://ex.co/l.png",
    "splashBackgroundColor": "#000000",
    "subtitle": "Easy to manage",
    "description": "Track and manage your cryptocurrency portfolio.",
    "screenshotUrls": [
      "https://ex.co/s1.png",
      "https://ex.co/s2.png",
      "https://ex.co/s3.png"
    ],
    "primaryCategory": "finance",
    "tags": ["finance"],
    "heroImageUrl": "https://ex.co/og.png",
    "tagline": "Save instantly",
    "ogTitle": "Example Mini App",
    "ogDescription": "Easy to manage portfolio.",
    "ogImageUrl": "https://ex.co/og.png",
    "noindex": false
  }
}
```

## Checklist

- [ ] Created `app/.well-known/farcaster.json/route.ts`
- [ ] Changed root key from `frame` to `miniapp`
- [ ] Added required fields: `name`, `homeUrl`, `iconUrl`, `splashImageUrl`, `splashBackgroundColor`
- [ ] Added recommended metadata: `subtitle`, `description`, `primaryCategory`
- [ ] Added screenshots (3:2 ratio)
- [ ] Added OG fields for social sharing
- [ ] Generated `accountAssociation` for your domain
- [ ] Updated environment variables
- [ ] Tested manifest at `https://yourapp.com/.well-known/farcaster.json`

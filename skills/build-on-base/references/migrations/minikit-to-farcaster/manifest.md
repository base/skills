# Manifest Migration

Change root key from `frame` to `miniapp` in `/.well-known/farcaster.json`.

## Before

```typescript
return Response.json({
  accountAssociation: { ... },
  frame: {
    version: "1",
    name: "My App",
    ...
  }
});
```

## After

```typescript
return Response.json({
  accountAssociation: { ... },
  miniapp: {
    version: "1",
    name: "My App",
    homeUrl: "https://yourapp.com",
    iconUrl: "https://yourapp.com/icon.png",
    splashImageUrl: "https://yourapp.com/splash.png",
    splashBackgroundColor: "#000000",
    // Optional
    subtitle: "Short tagline",
    description: "Longer description",
    primaryCategory: "utilities",
    webhookUrl: "https://yourapp.com/api/webhook",
  }
});
```

## Required Fields

- `version`: Always `"1"`
- `name`: App name (max 32 chars)
- `homeUrl`: Main app URL
- `iconUrl`: 1:1 ratio, min 200x200
- `splashImageUrl`: 1:1 ratio
- `splashBackgroundColor`: Hex color

## Categories

`games` | `social` | `finance` | `utilities` | `productivity` | `entertainment` | `news` | `shopping` | `health` | `education`

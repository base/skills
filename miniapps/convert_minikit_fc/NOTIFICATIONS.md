# Notifications Migration

MiniKit's `useNotification` hook abstracts server-side notification sending. With the Farcaster SDK, you implement this directly via webhooks.

## How Notifications Work

1. User adds your app via `sdk.actions.addMiniApp()`
2. You receive a `notificationDetails` object with `url` and `token`
3. Store these credentials in your database
4. Send notifications via POST request to the URL with the token

## Client-Side: Capture Notification Credentials

### Before (MiniKit)
```typescript
import { useAddFrame, useNotification } from '@coinbase/onchainkit/minikit';

function App() {
  const addFrame = useAddFrame();
  const sendNotification = useNotification();

  const handleAdd = async () => {
    const result = await addFrame();
    // MiniKit handled storage internally
  };

  const handleNotify = async () => {
    await sendNotification({
      title: 'Hello!',
      body: 'New message'
    });
  };
}
```

### After (Farcaster SDK)
```typescript
import { sdk } from '@farcaster/miniapp-sdk';

function App() {
  const handleAdd = async () => {
    const result = await sdk.actions.addMiniApp();
    
    if (result) {
      // Save credentials to your backend
      await fetch('/api/save-notification-token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          fid: sdk.context?.user?.fid,
          notificationUrl: result.url,
          notificationToken: result.token
        })
      });
    }
  };

  const handleNotify = async () => {
    // Trigger notification from your server
    await fetch('/api/send-notification', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        fid: sdk.context?.user?.fid,
        title: 'Hello!',
        body: 'New message'
      })
    });
  };
}
```

## Server-Side: Store and Send Notifications

### Database Schema (example with Prisma)

```prisma
model NotificationSubscription {
  id        String   @id @default(cuid())
  fid       Int      @unique
  url       String
  token     String
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt
}
```

### Save Token Endpoint

```typescript
// app/api/save-notification-token/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

export async function POST(req: NextRequest) {
  const { fid, notificationUrl, notificationToken } = await req.json();

  await prisma.notificationSubscription.upsert({
    where: { fid },
    update: {
      url: notificationUrl,
      token: notificationToken,
    },
    create: {
      fid,
      url: notificationUrl,
      token: notificationToken,
    },
  });

  return NextResponse.json({ success: true });
}
```

### Send Notification Endpoint

```typescript
// app/api/send-notification/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

export async function POST(req: NextRequest) {
  const { fid, title, body, targetUrl } = await req.json();

  // Get user's notification credentials
  const subscription = await prisma.notificationSubscription.findUnique({
    where: { fid }
  });

  if (!subscription) {
    return NextResponse.json(
      { error: 'User has not enabled notifications' },
      { status: 404 }
    );
  }

  // Send notification to Farcaster
  const response = await fetch(subscription.url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      notificationId: crypto.randomUUID(),
      title,
      body,
      targetUrl: targetUrl || process.env.NEXT_PUBLIC_URL,
      tokens: [subscription.token],
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    console.error('Notification failed:', error);
    return NextResponse.json({ error }, { status: response.status });
  }

  return NextResponse.json({ success: true });
}
```

## Notification Payload Format

```typescript
interface NotificationPayload {
  notificationId: string;  // Unique ID for this notification
  title: string;           // Notification title (max 32 chars)
  body: string;            // Notification body (max 128 chars)
  targetUrl: string;       // URL to open when tapped
  tokens: string[];        // Array of notification tokens
}
```

## Bulk Notifications

Send to multiple users at once:

```typescript
// app/api/broadcast-notification/route.ts
export async function POST(req: NextRequest) {
  const { title, body, targetUrl } = await req.json();

  // Get all subscriptions
  const subscriptions = await prisma.notificationSubscription.findMany();

  // Group by notification URL (different Farcaster clients may have different URLs)
  const byUrl = subscriptions.reduce((acc, sub) => {
    if (!acc[sub.url]) acc[sub.url] = [];
    acc[sub.url].push(sub.token);
    return acc;
  }, {} as Record<string, string[]>);

  // Send to each URL
  const results = await Promise.all(
    Object.entries(byUrl).map(async ([url, tokens]) => {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          notificationId: crypto.randomUUID(),
          title,
          body,
          targetUrl: targetUrl || process.env.NEXT_PUBLIC_URL,
          tokens,
        }),
      });
      return { url, success: response.ok, count: tokens.length };
    })
  );

  return NextResponse.json({ results });
}
```

## Webhook Handler

Handle notification-related webhooks from Farcaster:

```typescript
// app/api/webhook/route.ts
import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  const body = await req.json();

  switch (body.event) {
    case 'frame_added':
      // User added your app
      // body.notificationDetails contains { url, token }
      await saveNotificationCredentials(
        body.fid,
        body.notificationDetails
      );
      break;

    case 'frame_removed':
      // User removed your app
      await removeNotificationCredentials(body.fid);
      break;

    case 'notifications_disabled':
      // User disabled notifications
      await disableNotifications(body.fid);
      break;

    case 'notifications_enabled':
      // User re-enabled notifications
      // body.notificationDetails contains new { url, token }
      await saveNotificationCredentials(
        body.fid,
        body.notificationDetails
      );
      break;
  }

  return NextResponse.json({ success: true });
}
```

## Redis Alternative (Upstash)

If using Redis instead of a database:

```typescript
import { Redis } from '@upstash/redis';

const redis = Redis.fromEnv();

// Save
await redis.hset(`notifications:${fid}`, {
  url: notificationUrl,
  token: notificationToken
});

// Get
const data = await redis.hgetall(`notifications:${fid}`);

// Delete
await redis.del(`notifications:${fid}`);
```

## Checklist

- [ ] Created database table/Redis keys for notification credentials
- [ ] Implemented save-token endpoint
- [ ] Implemented send-notification endpoint
- [ ] Updated client to save credentials after `addMiniApp()`
- [ ] Updated client to call your API instead of `useNotification`
- [ ] Set up webhook handler for frame events
- [ ] Tested notification delivery

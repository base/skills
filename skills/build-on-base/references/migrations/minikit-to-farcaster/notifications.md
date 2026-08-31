# Notifications Migration

Server-side notification implementation when migrating from MiniKit to Farcaster SDK.

## Overview

In MiniKit, notifications were sent client-side via `useNotification()`. In the Farcaster SDK, all notifications must be sent server-side via the Farcaster notification API. This requires:

1. A server endpoint to handle notification requests
2. Farcaster notification webhook registration
3. User notification token management

## Server-Side Implementation

### 1. Register a Notification Webhook

Register your app's webhook URL with Farcaster to receive notification events:

```typescript
// POST to Farcaster's notification registration endpoint
const response = await fetch('https://api.farcaster.xyz/v1/frame-notifications', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${FARCASTER_API_KEY}`
  },
  body: JSON.stringify({
    url: 'https://your-app.com/api/webhook',
    // Your app's Farcaster account fid
    fid: YOUR_APP_FID
  })
});
```

### 2. Store User Notification Tokens

When users opt in to notifications, store their notification tokens:

```typescript
// In your webhook handler, save the notification token
app.post('/api/webhook', async (req, res) => {
  const { event, notificationDetails } = req.body;

  if (event === 'frame_added') {
    // Store the notification token for this user
    await db.userNotifications.upsert({
      fid: req.body.fid,
      token: notificationDetails.token,
      url: notificationDetails.url
    });
  }

  res.status(200).json({ ok: true });
});
```

### 3. Send Notifications

Send notifications from your server using stored tokens:

```typescript
app.post('/api/send-notification', async (req, res) => {
  const { title, body, targetFid } = req.body;

  // Look up the user's notification token
  const user = await db.userNotifications.findByFid(targetFid);
  if (!user) {
    return res.status(404).json({ error: 'User not subscribed' });
  }

  // Send via Farcaster's notification API
  const response = await fetch('https://api.farcaster.xyz/v1/frame-notifications', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${FARCASTER_API_KEY}`
    },
    body: JSON.stringify({
      notificationId: crypto.randomUUID(),
      title,
      body,
      targetUrl: 'https://your-app.com',
      tokens: [user.token]
    })
  });

  const result = await response.json();

  // Handle expired or invalid tokens
  if (result.invalidTokens) {
    await db.userNotifications.deleteByTokens(result.invalidTokens);
  }

  res.status(200).json({ ok: true });
});
```

## Client-Side Trigger

The client only needs to call your server endpoint:

```typescript
function NotifyButton({ targetFid }: { targetFid: number }) {
  const handleNotify = async () => {
    await fetch('/api/send-notification', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: 'Hello!',
        body: 'You have a new message',
        targetFid
      })
    });
  };

  return <button onClick={handleNotify}>Send Notification</button>;
}
```

## Key Differences from MiniKit

| | MiniKit | Farcaster SDK |
|---|---|---|
| Sending | Client-side `useNotification()` | Server-side HTTP API |
| Authentication | Implicit via MiniKit context | Explicit API key |
| Token management | Handled by MiniKit | You store notification tokens |
| Webhook | Not required | Required for receiving events |

## Security Notes

- Never expose your Farcaster API key to the client
- Validate all notification requests on the server
- Implement rate limiting to prevent notification spam
- Handle token expiration gracefully

# Notifications Migration

MiniKit's `useNotification` hook does not have a direct one-to-one client-side replacement in the Farcaster Mini App SDK.

When migrating notification functionality, move notification sending logic to your backend instead of sending notifications directly from the client.

## Migration Summary

### Before

MiniKit apps may use `useNotification()` from `@coinbase/onchainkit/minikit` inside client components.

### After

Farcaster Mini Apps should trigger a backend endpoint from the client. The backend is responsible for handling notification delivery.

## Recommended Pattern

Create a server endpoint, such as:

`POST /api/send-notification`

Then call that endpoint from your client when a notification should be sent.

Example client-side trigger:

```typescript
async function sendNotification() {
  await fetch('/api/send-notification', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      title: 'Hello!',
      body: 'You have a new message',
    }),
  });
}
```

## Important Notes

- Do not keep notification credentials or secrets in client-side code.
- Validate the user and request on the backend before sending notifications.
- Avoid blindly forwarding arbitrary client-provided notification content.
- Treat notification sending as a server-side capability.

## Migration Checklist

- Remove `useNotification` imports from `@coinbase/onchainkit/minikit`.
- Replace direct client notification calls with a backend API call.
- Add backend validation before sending notifications.
- Keep any notification tokens, secrets, or credentials server-side.

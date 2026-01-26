# Quick Auth Migration

`useAuthenticate` → `sdk.quickAuth`

## Client

```typescript
import { sdk } from '@farcaster/miniapp-sdk';

// Make authenticated request (recommended)
const res = await sdk.quickAuth.fetch('/api/auth');

// Or get token directly
const { token } = await sdk.quickAuth.getToken();
// token is a string (JWT)
```

## Types

```typescript
// getToken() returns { token: string }
const { token } = await sdk.quickAuth.getToken();
const [authToken, setAuthToken] = useState<string | null>(null);
setAuthToken(token);
```

## When to Use

| Endpoint | Method | Why |
|----------|--------|-----|
| Auth-protected API routes | `sdk.quickAuth.fetch()` | Auto-adds `Authorization: Bearer <jwt>` header |
| Public endpoints | Regular `fetch()` | No auth needed |

**401 "Missing token" error?** → Use `sdk.quickAuth.fetch()` instead of `fetch()`.

## Server (Next.js)

```bash
npm install @farcaster/quick-auth
```

```typescript
// app/api/auth/route.ts
import { createClient } from '@farcaster/quick-auth';
import { NextRequest, NextResponse } from 'next/server';

const client = createClient();

export async function GET(request: NextRequest) {
  const auth = request.headers.get('Authorization');
  if (!auth?.startsWith('Bearer ')) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  try {
    const payload = await client.verifyJwt({
      token: auth.split(' ')[1],
      domain: 'your-domain.com',
    });
    return NextResponse.json({ fid: payload.sub });
  } catch {
    return NextResponse.json({ error: 'Invalid token' }, { status: 401 });
  }
}
```

See [Farcaster Quick Auth docs](https://miniapps.farcaster.xyz/docs/sdk/quick-auth).

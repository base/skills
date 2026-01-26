# Conversion Examples

## Contents

- [Social Actions](#social-actions)
- [User Profile](#user-profile)
- [App Initialization](#app-initialization)
- [Primary Button (Breaking Change)](#primary-button-breaking-change)
- [Sign-In Flow](#sign-in-flow)
- [SafeArea Component](#safearea-component) (conditional)
- [Add Mini App](#add-mini-app)

---

## Social Actions

**Before:**
```typescript
import { useClose, useOpenUrl, useViewProfile } from '@coinbase/onchainkit/minikit';

function Actions({ fid }) {
  const close = useClose();
  const viewProfile = useViewProfile();
  return (
    <>
      <button onClick={() => viewProfile(fid)}>Profile</button>
      <button onClick={close}>Close</button>
    </>
  );
}
```

**After:**
```typescript
import { sdk } from '@farcaster/miniapp-sdk';

function Actions({ fid }) {
  return (
    <>
      <button onClick={() => sdk.actions.viewProfile({ fid })}>Profile</button>
      <button onClick={() => sdk.actions.close()}>Close</button>
    </>
  );
}
```

---

## User Profile

**Before:**
```typescript
const { context } = useMiniKit();
const { fid, username } = context?.user ?? {};
```

**After:**
```typescript
const [user, setUser] = useState(null);

useEffect(() => {
  const load = async () => {
    const ctx = await sdk.context;
    setUser(ctx?.user);
  };
  load();
}, []);

const { fid, username } = user ?? {};
```

Or use MiniAppProvider (see [PROVIDER.md](PROVIDER.md)):
```typescript
import { useMiniAppContext } from '@/components/providers/MiniAppProvider';

const miniAppContext = useMiniAppContext();
const { fid, username } = miniAppContext?.context?.user ?? {};
```

---

## App Initialization

**Before:**
```typescript
const { setFrameReady, context, isSDKLoaded } = useMiniKit();

useEffect(() => {
  if (isSDKLoaded) setFrameReady();
}, [isSDKLoaded]);
```

**After:**
```typescript
const [ready, setReady] = useState(false);
const [context, setContext] = useState(null);

useEffect(() => {
  const init = async () => {
    const inMiniApp = await sdk.isInMiniApp();
    if (inMiniApp) {
      const ctx = await sdk.context;
      setContext(ctx);
      await sdk.actions.ready();
    }
    setReady(true);
  };
  init();
}, []);
```

---

## Primary Button (Breaking Change)

**Before:**
```typescript
usePrimaryButton(
  { text: `Clicked ${count}`, disabled: false },
  () => setCount(c => c + 1)
);
```

**After (no callback support):**
```typescript
useEffect(() => {
  const setup = async () => {
    await sdk.actions.setPrimaryButton({
      text: "Action",
      disabled: false,
      hidden: false,
      loading: false
    });
  };
  setup();
}, []);

// Use regular React buttons for click handling
```

---

## Sign-In Flow

**Before:**
```typescript
const { signIn } = useAuthenticate();
const result = await signIn({ nonce });
if (result === false) { /* failed */ }
```

**After (Quick Auth):**
```typescript
const { token } = await sdk.quickAuth.getToken();
await fetch('/api/auth', {
  headers: { Authorization: `Bearer ${token}` }
});
```

Or use authenticated fetch:
```typescript
const res = await sdk.quickAuth.fetch('/api/auth');
```

---

## SafeArea Component

**Only if the project imports `SafeArea` from OnchainKit:**

**Before:**
```typescript
import { SafeArea } from '@coinbase/onchainkit/minikit';
<SafeArea>{children}</SafeArea>
```

**After:**
```typescript
import { SafeArea } from '@/components/SafeArea';
<SafeArea>{children}</SafeArea>
```

Create `src/components/SafeArea.tsx` — see [SAFEAREA.md](SAFEAREA.md) for the full component code.

**If project does NOT use SafeArea:** Skip this step.

---

## Add Mini App

**Before:**
```typescript
const addFrame = useAddFrame();
const result = await addFrame();
```

**After:**
```typescript
const result = await sdk.actions.addMiniApp();
if (result) {
  saveTokenToServer(result.url, result.token);
}
```

# Conversion Examples

## Contents
- Social actions
- User profile
- App initialization
- Primary button
- Sign-in flow
- Safe area insets

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

Or use FrameProvider (see [PROVIDER.md](PROVIDER.md)):
```typescript
import { useFrameContext } from '@/components/providers/FrameProvider';

const frameContext = useFrameContext();
const { fid, username } = frameContext?.context?.user ?? {};
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

## Safe Area Insets

**Before:**
```typescript
const { context } = useMiniKit();
const insets = context?.client?.safeAreaInsets;
```

**After:**
```typescript
const [insets, setInsets] = useState(null);

useEffect(() => {
  const load = async () => {
    const ctx = await sdk.context;
    setInsets(ctx?.client?.safeAreaInsets);
  };
  load();
}, []);
```

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

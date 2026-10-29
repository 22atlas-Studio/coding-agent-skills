---
name: react-expo-gotchas
description: Hard-won React, Expo, Expo Router, NativeWind, EAS, Next.js and Vercel gotchas from shipped client apps. Load before writing or debugging any React, React Native, Expo, Expo Router, NativeWind, EAS build, Metro, TanStack Query, Recharts, or Next.js App Router code.
user_invocable: false
---

# React / Expo

Extracted from the global CLAUDE.md on 2026-07-26 as part of the
Claude 5 progressive-disclosure prune. These are gotchas, not conventions.

- stack: React + TypeScript + Tailwind + Vite (web); Expo Router + Supabase (mobile)
- conditional rendering > CSS visibility/hidden (avoids Tailwind conflicts)
- React Router: `navigate(-1)` from `useNavigate()`, NEVER raw `window.history.back()` (bfcache-aware, route-state-aware). Direct `history.back()` blanks the screen on bfcache restore in real Chrome (not headless).
- React 19 `useRef`: provide explicit initial value - `useRef<T>(undefined)` not `useRef<T>()`
- Recharts SVG props: cannot use CSS custom properties for `stroke`/`fill` - use literal hex
- `.npmrc`: add `legacy-peer-deps=true` for React 19 peer conflicts
- React Native `Linking.openURL`: never bare `onPress={() => Linking.openURL(url)}` - `canOpenURL` first + try/catch + Alert
- RN `Alert.alert` is a NO-OP on react-native-web: on any Expo-web/PWA export a screen that surfaces errors only via `Alert.alert` shows ZERO feedback (a failed sign-in looks like a dead button). Render errors INLINE (state + `<Text accessibilityRole="alert">`) on any web-exported screen; reserve Alert for native-only paths.
- `expo-print`: escape HTML in user content before injecting into `<pre>` (`&`, `<`, `>`)
- TanStack Query + `useEffect` ordering: `useQuery` MUST be declared before any `useEffect` that uses its data (TS2448)
- `@expo-google-fonts/<font>`: `useFonts()` in root `_layout.tsx` + `SplashScreen.preventAutoHideAsync()` + null guard - without `useFonts()`, fonts silently fall back to system defaults
- Expo Router route groups: EVERY group (`(auth)`, `(app)`) MUST have a `_layout.tsx`, otherwise back button walks through old screens; use `router.replace()` (not `push`) for auth-flow steps. NEVER use shell brace expansion to create groups - bash escapes parens.
- Expo Router custom tab bar: filter by explicit `VISIBLE_TABS` array; `href: null` routes still appear in `state.routes`.
- Expo Router cross-tab navigation: `router.push` works on native, NOT on web preview - test on phone.
- Expo Router client apps run only from `~/projects/<app>/`. Never rsync a standalone app back into the monorepo it was extracted from. Metro config needs `projectRoot = __dirname` + `watchFolders = [__dirname]` when the standalone project layout requires it.
- EAS cloud builds: local `.env` NOT available - set all `EXPO_PUBLIC_*` via `eas env:create --visibility plaintext --environment preview`
- EAS `eas.json`: every build profile that consumes env MUST set `environment: <name>` (e.g. `preview`) or the build silently ships with undefined `EXPO_PUBLIC_*` config - verify the resolved env in the build log, don't assume the profile inherited it
- Expo push `sent=N` means EXPO ACCEPTED THE BATCH, not that N phones buzzed - a DeviceNotRegistered token still counts as sent. Capture per-ticket ids + poll the receipts endpoint to prune dead tokens; until then only the user's own "I got it" closes the loop (say so rather than calling it verified).
- iOS "No signing certificate found" x32 + "PLA Update available" collapse to ONE account-level root cause: an unaccepted Apple Developer Program License Agreement blocks cert issuance. NEVER regenerate a distribution cert as the workaround - it burns a slot and fixes nothing.
- EAS/S3 signed artifact URLs expire ~15 min (`X-Amz-Expires=900`): "can't see the APK" is usually a stale link, not a build failure - download in-window or hand off a locally-saved copy
- React Native platform detection: `Platform.OS === 'web'` (NOT `typeof window !== 'undefined'` - RN has `window` but no `sessionStorage`)
- NativeWind v4: `babel.config.js` MUST have `presets: [['babel-preset-expo', { jsxImportSource: 'nativewind' }], 'nativewind/babel']`. Metro: `require('nativewind/dist/metro')` NOT `nativewind/metro`.
- react-native-reanimated in Expo Go: worklets crash - use RN built-in `Animated` (`spring`, `timing`, `loop`) with `useNativeDriver: true`. Reanimated only works in EAS dev client builds.
- Animated wrapper + Pressable: visual styles (bg, padding, radius) on INNER View, not on Animated.View - otherwise no hit area.
- React Native `fetch` does NOT support streams - SSE silently fails; use non-streaming JSON or `supabase.functions.invoke`
- Expo Go horizontal ScrollView clipping: chips get vertically clipped first render - `overflow: 'visible'` on ScrollView + `paddingVertical: 4` on contentContainerStyle
- React Native markdown: don't use `react-native-markdown-display` (broken deps) or `react-native-marked` (white film); write a ~70-line custom `ChatMarkdown` with native `<Text>`/`<View>`
- Figma design tokens: ALWAYS pull exact colors via `get_design_context` MCP before writing UI - assumed values are always wrong; set up `tailwind.config.js` + `colors.ts` first
- Figma Dev-Mode MCP `get_metadata`/`get_design_context` can return multi-MB payloads - grep the saved tool-results file for node IDs instead of re-reading inline; prefer Dev-Mode MCP over third-party "Figma to Code" clipboard plugins for parity capture
- read `node_modules/next/dist/docs/` before trusting training data on any Next.js API - it contradicted training data 3x in one build (Middleware renamed to `proxy.ts` in Next 16, async `cookies()`, `unstable_retry()` over `reset()`)
- put a `server-only` fence on Supabase/server clients: it converts an accidental client-side import into a BUILD error instead of a runtime crash (caught 2 real bugs). Split the module when only part is server-bound - the write path is server-only, its vocabulary strings are not.
- `?? 'fallback'` does NOT catch empty string `''` - a `display_name` of `''` rendered a 0x0 invisible unclickable link that only a live browser walk surfaced. Guard on falsiness, not nullishness, for display strings.
- `create-next-app` in WSL: add `--no-turbopack`
- kill dev servers by PORT (`fuser -k <port>/tcp`), NOT `pkill -f "next start"`: pkill can silently fail (exit 144 poisons compound-command exit codes) and the OLD build keeps serving the port, so you false-verify a fix against stale code. KILLING AND RESTARTING IS NOT PROOF EITHER: after the restart, fetch the bundle/route table over HTTP and grep for a string only THIS round introduces - never trust the process. A stale uvicorn on 8000 plus a stale `vite preview` on 4200 (both from a PREVIOUS session) served the old route table and produced an entire walk of phantom failures (example-app 2026-07-24)
- custom drag UI (slider thumbs, resize handles): setPointerCapture on the element's pointerdown + handle move/up/cancel ON it gated by stored pointerId + touch-action:none; container-level onPointerMove/Leave silently drops fast drags that exit the track
- timer-driven UI replay: advance the animation cursor from a ref INSIDE the setInterval body, NEVER inside a setState updater (React may double-invoke updaters, doubling side effects); guard one-shot terminal events with a ref
- self-hosted Next/systemd deploy-is-real check: verify BUILD_ID mtime + new route present in `.next/server` + service ActiveEnterTimestamp > build time BEFORE claiming a deploy landed (a git pull/autosync alone can leave the old build serving)
- vercel CLI deploy timing out client-side does NOT kill the server-side build - poll `vercel ls` until Ready instead of re-running (re-run = double deploy)

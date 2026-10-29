---
name: flutter-dart-gotchas
description: "Flutter and Dart build gotchas from shipped client apps: google-services wiring, flutter_local_notifications desugaring, multi-flavor launcher activities, analyze/CI scope traps, Firebase iOS white-screen pbxproj membership, AdMob init crashes, tester debug-vs-release sizing. Load before any Flutter, Dart, or pubspec work."
user_invocable: false
---

# Flutter / Dart

Extracted from the global CLAUDE.md on 2026-07-26 as part of the
Claude 5 progressive-disclosure prune. These are gotchas, not conventions.

- Dart MCP: `mcp__dart__run_tests`, `mcp__dart__analyze_files`, `mcp__dart__pub` over shell
- `google-services.json` required by Gradle's `com.google.gms.google-services` plugin even when Firebase uses `--dart-define` - generate minimal JSON from .env
- `flutter_local_notifications` 18.x: `coreLibraryDesugaringEnabled true` + `coreLibraryDesugaring 'com.android.tools:desugar_jdk_libs:2.1.4'`
- Debug APKs with heavy native SDKs (Samsung Health, Firebase, AdMob): 196MB+, OOM-kill on emulators - use real physical devices
- tester builds: READ the build config before picking debug vs release - a release block with no minify/shrink that signs with `signingConfigs.getByName("debug")` is BOTH safe and sign-in-capable at ~1/3 the size (58.6MB vs 172MB). Then verify the APK's signature SHA-1 matches the registered key (`apksigner verify --print-certs`) so Google Sign-In resolves its OAuth client, and say plainly that the build is verified-but-NOT-device-verified.
- Dart exhaustive switches: adding a new enum value breaks every switch - grep `switch (enumName)` first
- Multi-flavor builds (phone/wear): launcher activity may be `PhoneMainActivity` not `MainActivity` - `adb shell pm dump <pkg> | grep MAIN`; CI build needs `--flavor phone`
- CI analyze: `--no-fatal-warnings` is unreliable (exits 1 in CI, 0 locally) - grep `" error •"` instead
- `flutter analyze` scope: always run full (not file-scoped) before pushing - file-scoped misses cross-file errors AND can cold-start-hang the Dart analysis server 20+ min ("Analyzing N items..." no progress); full analyze completes in ~2s once the server is warm. Kill a hung file-scoped run, run `flutter test` (kernel already cached), then full `flutter analyze`.
- `health` ^11.0.0: unified Health Connect (Android) + HealthKit (iOS) - avoids separate Kotlin/Swift code
- Flutter+Firebase iOS WHITE SCREEN on launch: `GoogleService-Info.plist` must be a Runner TARGET member (pbxproj file ref + build file + Copy Bundle Resources), not just in the folder - else `FirebaseApp.configure()` throws and `main()` dies before `runApp` (silent blank screen in release). Durable pbxproj edit, not Xcode-GUI add.
- iOS AdMob launch crash (`GADInvalidInitializationException`): use the iOS test app id `ca-app-pub-3940256099942544~1458002511` (iOS analogue of the Android MobileAdsInitProvider crash)
- first iOS TestFlight build: tracer-bullet it - internal testing needs no Apple review and no working sign-in; ship build 1 to prove signing+upload+processing, wire OAuth/features in later builds. Inherited bundle id bound to a prior dev's team -> re-namespace under your own team, don't block on a transfer.

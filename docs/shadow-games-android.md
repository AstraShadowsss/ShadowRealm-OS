# Shadow Games for Android

Nine offline games with touch controls and local high scores. Shadow Games 1.0.1 runs on Android 7.0 or later with an up-to-date Android System WebView. Pinball plays in portrait; the other games play in landscape. The app requests no Internet permission and has no accounts, advertisements or analytics.

## Download and install

1. Download **ShadowGames-Android.apk** from the [Android release](https://github.com/AstraShadowsss/ShadowRealm-OS/releases/tag/shadow-games-android-v1.0.1).
2. Open it from Downloads or your file manager. If Android asks, enable **Allow from this source** for the app opening the file.
3. Return to the installer, tap **Install**, and open **Shadow Games**. You can disable **Allow from this source** afterward.

Developer mode is unnecessary for installation on the phone. Leave Play Protect enabled. An installation of the previous official preview can be updated in place without clearing its scores. Uninstalling the app deletes its local data.

## What's new

- Equal Pinball flippers, a centered Launch button and simultaneous touch controls.
- Landscape controls beside the playfield, including a direction pad for Circuit Chase and Snake.
- Twelve different rounded Marble Reactor tracks with a complete final stage.
- Three Skull Invaders enemy types and boss patterns, boss health bars, shields, repairs and temporary shot upgrades.
- Spider Solitaire stack dragging, buffered Snake turns and Android Back navigation fixes.

## Screenshots

Captured from the installed 1.0.1 APK in the Android emulator. Tap a game image to open it at full size.

<img src="../screenshots/android/game-menu.png?v=20261123c" alt="Shadow Games selection menu" width="300">

### Shadow Pinball

[![Shadow Pinball on Android](../screenshots/android/shadow-pinball.png?v=20261123c)](../screenshots/android/shadow-pinball.png)

### Skull Invaders

[![Skull Invaders on Android](../screenshots/android/skull-invaders.png?v=20261123c)](../screenshots/android/skull-invaders.png)

### Shadow Runner

[![Shadow Runner on Android](../screenshots/android/shadow-runner.png?v=20261123c)](../screenshots/android/shadow-runner.png)

### Neon Ascent

[![Neon Ascent on Android](../screenshots/android/neon-ascent.png?v=20261123c)](../screenshots/android/neon-ascent.png)

### Neon Breaker

[![Neon Breaker on Android](../screenshots/android/neon-breaker.png?v=20261123c)](../screenshots/android/neon-breaker.png)

### Shadow Snake

[![Shadow Snake on Android](../screenshots/android/shadow-snake.png?v=20261123c)](../screenshots/android/shadow-snake.png)

### Circuit Chase

[![Circuit Chase on Android](../screenshots/android/circuit-chase.png?v=20261123c)](../screenshots/android/circuit-chase.png)

### Shadow Spider Solitaire

[![Shadow Spider Solitaire on Android](../screenshots/android/shadow-solitaire.png?v=20261123c)](../screenshots/android/shadow-solitaire.png)

### Marble Reactor

[![Marble Reactor on Android](../screenshots/android/marble-reactor.png?v=20261123c)](../screenshots/android/marble-reactor.png)

## USB installation

Install [Android SDK Platform Tools](https://developer.android.com/tools/releases/platform-tools) on your computer. On the phone, tap **Build number** seven times under **About phone** (sometimes **Software information**), then enable **USB debugging** in **Developer options**. Connect and unlock the phone, approve your computer, and run `adb devices`. Install with `adb install -r ShadowGames-Android.apk`. Turn off USB debugging afterward.

## Build and validation

- App ID: `com.shadowgames.mobile`
- Version: **1.0.1** (version code 2).
- Distribution: debug-signed sideload preview, using the same certificate as 1.0.0.
- Tests: all nine games rendered in the installed APK; touch layout, Pinball multitouch, Spider stack dragging, pause and Back navigation passed. Separate rule checks cover win/loss transitions, Snake wrapping, all twelve Marble stages and the Pinball ball limit.
- Test limits: one Android emulator/device profile; physical phones and older WebView versions remain untested. The audio engine started successfully; audible output was not checked in this emulator run.
- APK SHA-256: `cbfbe6b6a1eb7084e5ccda0a20518297125059529e8c13852b6af7b22e86acd0`

The [MIT game license](shadow-games-android-license.txt) accompanies the download.

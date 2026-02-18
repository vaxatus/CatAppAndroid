#!/usr/bin/env bash
# Build, optionally start emulator, install app and run automation tests.
# Usage:
#   ./scripts/run-and-test.sh              # build only (no device needed)
#   ./scripts/run-and-test.sh install     # build + install (device/emulator required)
#   ./scripts/run-and-test.sh test        # build + install + connectedAndroidTest
#   ./scripts/run-and-test.sh emulator    # start first AVD in background, then install + test

set -e
cd "$(dirname "$0")/.."
export JAVA_HOME="${JAVA_HOME:-$(/usr/libexec/java_home -v 23 2>/dev/null || /usr/libexec/java_home -v 21 2>/dev/null || /usr/libexec/java_home 2>/dev/null)}"
export ANDROID_HOME="${ANDROID_HOME:-$HOME/Library/Android/sdk}"
export PATH="$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator:$PATH"

./gradlew assembleDebug

case "${1:-}" in
  install)
    if ! adb devices | grep -q 'device$'; then
      echo "No device/emulator. Start one (e.g. Android Studio > Device Manager) and run again."
      exit 1
    fi
    ./gradlew installDebug
    echo "App installed. Launch: adb shell am start -n com.vaxatus.cat.myapplication/.MainActivity"
    ;;
  test)
    if ! adb devices | grep -q 'device$'; then
      echo "No device/emulator. Start one and run again, or use: $0 emulator"
      exit 1
    fi
    ./gradlew installDebug connectedDebugAndroidTest
    echo "Tests finished. Report: app/build/reports/androidTests/connected/index.html"
    ;;
  emulator)
    AVD=$("$ANDROID_HOME/emulator/emulator" -list-avds | head -1)
    if [ -z "$AVD" ]; then
      echo "No AVD found. Create one in Android Studio > Device Manager."
      exit 1
    fi
    echo "Starting AVD: $AVD"
    "$ANDROID_HOME/emulator/emulator" -avd "$AVD" -no-snapshot-load &
    EMU_PID=$!
    echo "Waiting for emulator to boot..."
    adb wait-for-device
    while [ "$(adb shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" != "1" ]; do sleep 2; done
    ./gradlew installDebug connectedDebugAndroidTest
    kill $EMU_PID 2>/dev/null || true
    echo "Done. Report: app/build/reports/androidTests/connected/index.html"
    ;;
  *)
    echo "Built successfully. Next:"
    echo "  1. Start emulator or connect device"
    echo "  2. ./scripts/run-and-test.sh install   # install app"
    echo "  3. ./scripts/run-and-test.sh test      # run UI automation tests"
    echo "  Or: ./scripts/run-and-test.sh emulator # start AVD, install and test"
    ;;
esac

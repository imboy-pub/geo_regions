#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
command -v flutter >/dev/null 2>&1 || { echo 'Install Flutter stable and add flutter to PATH.' >&2; exit 127; }
if [[ ! -d web ]]; then
  geo_demo_temp="$(mktemp -d "${TMPDIR:-/tmp}/geo-regions-web.XXXXXX")"
  trap 'rm -rf -- "$geo_demo_temp"' EXIT
  flutter create --platforms=web --project-name=geo_regions_demo --no-pub "$geo_demo_temp"
  # Copy only generated platform files; preserve our sources, tests and SDK-only pubspec.
  cp -R -- "$geo_demo_temp/web" ./web
fi
flutter pub get
printf '%s\n' 'Ready: flutter run -d chrome' 'Verify: dart format lib test && flutter analyze && flutter test && flutter build web --release'

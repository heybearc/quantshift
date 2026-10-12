#!/bin/bash
# Release testing for QuantShift.
# Usage: scripts/release-test.sh [gate|auth|admin|trading|full]
# Set RELEASE_BASE_URL to the current STANDBY URL. It wins over .env.test.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/apps/web"

AREA="${1:-gate}"

if [[ -f .env.test ]]; then
  set -a
  # shellcheck disable=SC1091
  source <(grep -E '^[A-Za-z_][A-Za-z0-9_]*=' .env.test)
  set +a
fi

if [[ -n "${RELEASE_BASE_URL:-}" ]]; then
  export BASE_URL="$RELEASE_BASE_URL"
fi

export BASE_URL="${BASE_URL:-http://localhost:3001}"

echo "Release tests ($AREA) against $BASE_URL"

case "$AREA" in
  gate)
    exec npx playwright test tests/release-gate.spec.ts --workers=1
    ;;
  auth)
    exec npx playwright test tests/release-gate.spec.ts tests/auth-pages.spec.ts --workers=1
    ;;
  admin)
    exec npx playwright test tests/release-gate.spec.ts tests/admin-pages.spec.ts --workers=1
    ;;
  trading)
    exec npx playwright test tests/release-gate.spec.ts tests/trading-features.spec.ts --workers=1
    ;;
  full)
    export CI="${CI:-1}"
    exec npx playwright test --workers=1
    ;;
  *)
    echo "usage: scripts/release-test.sh [gate|auth|admin|trading|full]" >&2
    exit 2
    ;;
esac

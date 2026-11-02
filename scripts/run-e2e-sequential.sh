#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
E2E_DIR="$ROOT_DIR/bgg-shop-frontend/tests/e2e"
REPORT_DIR="$ROOT_DIR/test-results/e2e-sequential-$(date +%Y%m%d-%H%M%S)"
FRONTEND_DIR="$ROOT_DIR/bgg-shop-frontend"
mkdir -p "$REPORT_DIR"

echo "Running Playwright E2E tests sequentially from $E2E_DIR"

# Find test files matching *.spec.ts or *.spec.tsx
mapfile -t tests < <(find "$E2E_DIR" -type f -name "*.spec.ts" -o -name "*.spec.tsx" | sort)

if [ ${#tests[@]} -eq 0 ]; then
  echo "No E2E test files found in $E2E_DIR"
  exit 1
fi

for testfile in "${tests[@]}"; do
  rel=$(realpath --relative-to="$ROOT_DIR" "$testfile")
  # Path relative to frontend package root for running Playwright there
  rel_frontend=$(realpath --relative-to="$FRONTEND_DIR" "$testfile")
  echo "\n=== Running test: $rel ==="

  # Run single test with Playwright. Try chromium project first, fallback to default projects
  rc=0
  # Run Playwright from the frontend package directory so it picks up local config
  (cd "$FRONTEND_DIR" && npx playwright test "$rel_frontend" --project=chromium --workers=1 --reporter=list) || rc=$?
  if [ "$rc" -ne 0 ]; then
    echo "Initial run with --project=chromium failed (rc=$rc). Retrying without --project..."
    rc=0
    (cd "$FRONTEND_DIR" && npx playwright test "$rel_frontend" --workers=1 --reporter=list) || rc=$?
  fi

  # Copy artifacts for this run (if any)
  if [ -d "$ROOT_DIR/test-results" ]; then
    echo "Copying Playwright artifacts to $REPORT_DIR"
    cp -r "$ROOT_DIR/test-results" "$REPORT_DIR/$(basename "$testfile" .spec.ts)" 2>/dev/null || true
  fi

  # Capture BFF and Core logs into the report directory for this test
  safe_name=$(basename "$testfile" | sed 's/[^a-zA-Z0-9_.-]/_/g')
  mkdir -p "$REPORT_DIR/$safe_name/logs"
  echo "Collecting BFF and Core logs for $safe_name"
  # Try podman logs first, fallback to docker logs if podman not available
  # Number of tail lines to capture; default 50 (override with env TAIL_LINES)
  TAIL_LINES=${TAIL_LINES:-50}
  if command -v podman >/dev/null 2>&1; then
    podman logs --tail "$TAIL_LINES" saleor_bff > "$REPORT_DIR/$safe_name/logs/saleor_bff.log" 2>&1 || true
    podman logs --tail "$TAIL_LINES" saleor_api > "$REPORT_DIR/$safe_name/logs/saleor_api.log" 2>&1 || true
  else
    docker logs --tail "$TAIL_LINES" saleor_bff > "$REPORT_DIR/$safe_name/logs/saleor_bff.log" 2>&1 || true
    docker logs --tail "$TAIL_LINES" saleor_api > "$REPORT_DIR/$safe_name/logs/saleor_api.log" 2>&1 || true
  fi

  if [ "$rc" -ne 0 ]; then
    echo "Test failed: $rel (exit $rc)"
    echo "Artifacts saved under: $REPORT_DIR"
    echo "Stopping sequential run for investigation."
    exit $rc
  fi

  echo "Test passed: $rel"
done

echo "All sequential E2E tests passed. Artifacts (if any) in $REPORT_DIR"
exit 0

#!/usr/bin/env bash
# Build the Go->WASM UI. Prefers TinyGo (much smaller binary); falls back to Go.
set -euo pipefail
cd "$(dirname "$0")"

if command -v tinygo >/dev/null 2>&1; then
  echo "Building with TinyGo…"
  tinygo build -o app.wasm -target wasm -no-debug ./main.go
  cp "$(tinygo env TINYGOROOT)/targets/wasm_exec.js" ./wasm_exec.js
else
  echo "TinyGo not found — falling back to the Go toolchain (larger binary)…"
  GOOS=js GOARCH=wasm go build -o app.wasm ./main.go
  # wasm_exec.js moved to lib/wasm in Go 1.24+; try both locations.
  GOROOT="$(go env GOROOT)"
  cp "${GOROOT}/lib/wasm/wasm_exec.js" ./wasm_exec.js 2>/dev/null \
    || cp "${GOROOT}/misc/wasm/wasm_exec.js" ./wasm_exec.js
fi

echo "Built app.wasm + wasm_exec.js."
echo "Serve this directory, e.g.:  python3 -m http.server 8080"

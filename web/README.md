# web/ — Go → WebAssembly UI

A minimal browser UI that calls the AI service's REST API. **Optional and non-blocking** — the
REST API is the contract, so this can be replaced with plain HTML/JS or React at any time.

## Build & run

```bash
./build.sh                    # -> app.wasm + wasm_exec.js (uses TinyGo if available)
python3 -m http.server 8080   # serve this dir, then open http://localhost:8080
```

Enter the `X-API-Key` (the `AI_SERVICE_API_KEY` from your `.env`) and ask a question.

## Notes

- `app.wasm` and `wasm_exec.js` are build artifacts (gitignored). Run `./build.sh` to (re)generate.
- The service's `ALLOWED_ORIGINS` must include this origin (`http://localhost:8080` by default) for
  CORS to allow the request.
- TinyGo is recommended to keep the binary small; the standard Go toolchain also works.

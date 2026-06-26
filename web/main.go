//go:build js && wasm

// Minimal Go->WASM UI for ai-platform-lab. Optional and non-blocking: the REST
// API is the contract, so this can be swapped for plain HTML/JS or React anytime.
//
// Build with TinyGo (small binary):  ./build.sh
package main

import (
	"encoding/json"
	"syscall/js"
)

const askURL = "http://localhost:8000/ask"

func main() {
	js.Global().Set("askQuestion", js.FuncOf(askQuestion))
	select {} // keep the Go runtime alive for callbacks
}

// askQuestion is wired to the Ask button. It POSTs to /ask and renders the answer.
func askQuestion(this js.Value, args []js.Value) any {
	doc := js.Global().Get("document")
	question := doc.Call("getElementById", "question").Get("value").String()
	apiKey := doc.Call("getElementById", "apikey").Get("value").String()
	out := doc.Call("getElementById", "output")
	out.Set("textContent", "Asking…")

	body, _ := json.Marshal(map[string]any{"question": question})
	opts := map[string]any{
		"method": "POST",
		"headers": map[string]any{
			"Content-Type": "application/json",
			"X-API-Key":    apiKey,
		},
		"body": string(body),
	}

	js.Global().Call("fetch", askURL, js.ValueOf(opts)).
		Call("then", js.FuncOf(func(_ js.Value, a []js.Value) any {
			return a[0].Call("json")
		})).
		Call("then", js.FuncOf(func(_ js.Value, a []js.Value) any {
			data := a[0]
			answer := data.Get("answer")
			if answer.IsUndefined() {
				out.Set("textContent", "Error: "+js.Global().Get("JSON").Call("stringify", data).String())
			} else {
				out.Set("textContent", answer.String())
			}
			return nil
		})).
		Call("catch", js.FuncOf(func(_ js.Value, a []js.Value) any {
			out.Set("textContent", "Request failed: "+a[0].Call("toString").String())
			return nil
		}))
	return nil
}

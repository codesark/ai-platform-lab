# MCP server

The platform's tools live in **one tool core** exposed two ways: natively to the agent, and over
an **MCP server** so any MCP host (Claude Desktop, Cursor, …) can use them.

## Planned surface

- **Tools:** `retrieve_docs`, `lookup`, `compute`
- **Resources:** corpus documents (`corpus://doc/{id}`)
- **Prompts:** an "answer-with-citations" template
- **Transports:** `stdio` (local hosts) and Streamable HTTP (remote, authenticated)

## How to connect

Documented here once the server lands — local hosts via `stdio` (e.g. the MCP Inspector or Claude
Desktop), remote clients via the authenticated HTTP endpoint.

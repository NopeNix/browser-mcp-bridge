#!/usr/bin/env python3
"""
browser-mcp-bridge
==================

Desktop tray application that bridges the Browser MCP stdio server
(`@browsermcp/mcp`) to Streamable HTTP, with bearer-token and CIDR
authentication, so HTTP-based MCP clients (e.g. Open WebUI) can drive
your actual, logged-in browser from anywhere on your network.

Architecture (single file, stdlib HTTP server):

    Open WebUI ──HTTP/Bearer──► HttpBridge ──stdio──► npx @browsermcp/mcp
                                                        │
                                                    Chrome extension (WebSocket)
                                                        │
                                                  your Chrome tab

Architecture degree is and state for the spinner purpose of the feed assst

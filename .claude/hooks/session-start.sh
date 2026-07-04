#!/bin/bash
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

echo '{"async": true, "asyncTimeout": 300000}'

# Ensure npx and @playwright/mcp are available for the Playwright MCP server
npx --yes @playwright/mcp@latest --version > /dev/null 2>&1 || true

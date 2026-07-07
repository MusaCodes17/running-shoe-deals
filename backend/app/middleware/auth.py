"""
Bearer-token auth middleware (R2.1 — the security pass).

Anton's trust model changes here from a *network* property ("only things that can
reach port 8000 can mutate") to an *application* property ("only requests carrying
the shared secret can mutate"). Every request to `/api/*` and the mounted `/mcp`
sub-app must present `Authorization: Bearer <ANTON_SECRET>`; a mismatch or absence
returns **401 with an empty body** (don't leak whether the path exists or why auth
failed). See `SECURITY_PASS_PLAN.md` and `docs/design_decisions.md` E1.

Why a *pure ASGI* middleware and not `BaseHTTPMiddleware` or a dependency:
- The app streams SSE (chat + scrape progress) and serves the `/mcp` Streamable
  HTTP transport. `BaseHTTPMiddleware` wraps/buffers the response body and is a
  known breaker of streaming responses — this middleware only inspects the request
  headers and forwards `receive`/`send` untouched, so streams pass through intact.
- A middleware (not a per-router dependency) covers *every* route, including the
  mounted `/mcp` sub-app, without per-router decoration. A top-level middleware
  wraps the whole ASGI app, so it sits outside the router that dispatches to the
  mount — one check guards both surfaces (asserted in `tests/test_auth.py`).

Registered *inside* CORS in `main.py` (added before `CORSMiddleware`, so CORS is
the outer wrapper) so that a 401 response still carries CORS headers and the
browser surfaces a clean 401 instead of an opaque CORS error.
"""
from __future__ import annotations

import os
import secrets

# Paths reachable without a token: the root banner and the liveness probes. These
# leak nothing sensitive and must stay open (a monitor/health check has no token).
# Everything else under /api/* and all of /mcp requires the bearer token.
PUBLIC_PATHS: frozenset[str] = frozenset({"/", "/health", "/api/health"})

_BEARER_PREFIX = "bearer "  # case-insensitive scheme match


class BearerAuthMiddleware:
    """
    Pure ASGI middleware enforcing `Authorization: Bearer <ANTON_SECRET>`.

    The secret is read once from the environment at construction (Starlette builds
    the middleware stack once at startup, so this is "read once at startup, not
    per-request"). An empty configured secret denies *everything* — belt-and-braces
    behind `main.require_anton_secret()`'s fail-fast, so a misconfigured server can
    never accidentally authorize with an empty token.
    """

    def __init__(self, app):
        self.app = app
        self.secret = os.getenv("ANTON_SECRET", "").strip()

    async def __call__(self, scope, receive, send):
        # Non-HTTP scopes (lifespan, and websockets if ever added) pass through.
        # There are no WebSocket endpoints today; add an explicit gate here before
        # introducing one (SECURITY_PASS_PLAN §4 task 2).
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # CORS preflight must never require the token, or the browser preflight
        # breaks. (Starlette's CORSMiddleware already answers real preflights before
        # us; this is defence for any OPTIONS that slips through.)
        if scope.get("method") == "OPTIONS":
            await self.app(scope, receive, send)
            return

        if scope.get("path") in PUBLIC_PATHS:
            await self.app(scope, receive, send)
            return

        if self._authorized(scope):
            await self.app(scope, receive, send)
            return

        await self._reject(send)

    def _authorized(self, scope) -> bool:
        if not self.secret:
            return False  # no secret configured → authorize nothing
        header = self._get_header(scope, b"authorization")
        if not header or not header.lower().startswith(_BEARER_PREFIX):
            return False
        presented = header[len(_BEARER_PREFIX):].strip()
        # Constant-time compare so a timing side channel can't leak the secret.
        return secrets.compare_digest(presented, self.secret)

    @staticmethod
    def _get_header(scope, name: bytes) -> str | None:
        for key, value in scope.get("headers", []):
            if key == name:
                return value.decode("latin-1")
        return None

    @staticmethod
    async def _reject(send) -> None:
        # 401 with an empty body — no `WWW-Authenticate`, no reason string.
        await send(
            {
                "type": "http.response.start",
                "status": 401,
                "headers": [(b"content-length", b"0")],
            }
        )
        await send({"type": "http.response.body", "body": b""})

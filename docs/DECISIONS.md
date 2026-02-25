# Architecture Decisions

## 2026-02-26

### D-001 Storage backend strategy
- Decision: Use `STORAGE_BACKEND=auto` by default.
- Behavior:
  - If R2 credentials exist and boto3 available -> use R2.
  - Else -> local storage fallback.
- Reason: Keep dev environment operational without breaking startup.

### D-002 Share asset access
- Decision: Keep bucket private; provide presigned GET URLs only.
- Reason: Prevent direct public bucket exposure and allow short-lived access.

### D-003 Share TTL
- Decision: Share token validity is fixed by `SHARE_TOKEN_TTL_HOURS` (default 24h).
- Reason: Product requirement and operational simplicity.

### D-004 Upload API flow
- Decision: Standard kiosk upload flow is `share/init -> share/upload -> share/finalize`.
- Reason: Explicit lifecycle, easier logging and failure recovery.

### D-005 Brand naming
- Decision: Use `viorafilm` as canonical brand name in product docs and operations.
- Reason: Branding consistency.

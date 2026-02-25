# Viorafilm Master Plan

## North Star
- Build a production-grade photobooth platform under the `viorafilm` brand.
- Match Durishot dashboard features, then exceed with stronger security and operations.

## Product Goals
1. Web dashboard login with strict role-based access.
2. Device-authenticated kiosk API only (no anonymous kiosk actions).
3. QR-based downloads for print/gif/video/original assets.
4. Share links valid for exactly 24 hours.
5. R2 private storage + presigned download URLs.
6. Approved devices only; unapproved devices blocked.
7. Offline grace policy: kiosk works up to 72 hours without internet, then locks.
8. OTA update/rollback for kiosk app.
9. AI mode added after core stability.

## Delivery Order (Do Not Change)
1. Production security + deployment baseline.
2. Durishot parity for dashboard modules.
3. Device authorization hardening.
4. Offline 72-hour lease lock.
5. OTA operationalization.
6. AI mode.

## Definition of Done (Global)
- Feature works end-to-end.
- Logs are present for success/failure paths.
- Permission boundaries verified.
- Migration/check pass.
- Manual test checklist updated.

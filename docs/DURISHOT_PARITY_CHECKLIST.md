# Durishot Parity Checklist

Status keys: `TODO`, `IN_PROGRESS`, `DONE`

| Area | Item | Status | Notes |
|---|---|---|---|
| Auth | Dashboard login/logout | DONE | Django session auth active |
| Auth | Role scopes (super/org/branch/viewer) | IN_PROGRESS | Base done, module-level edge checks pending |
| Sales | Daily/monthly summary cards | DONE | Implemented |
| Sales | Advanced filtering/export parity | IN_PROGRESS | Needs exact Durishot filter parity |
| Device | Device status table | IN_PROGRESS | Basic health exists, control actions pending |
| Coupon | Issue/delete/used/expired flows | IN_PROGRESS | Core done, UX parity pending |
| Photo | Photo management table | IN_PROGRESS | Works, needs final parity polish |
| Share | 24h link expiration | DONE | DB expiry + cleanup |
| Share | R2 private + presigned links | DONE | Implemented |
| Kiosk | Device approval gating | TODO | Must block unapproved runtime |
| Policy | Offline 72h lock | TODO | Planned last core security feature |
| OTA | Active/min-supported/rollback | IN_PROGRESS | Server side done, kiosk auto-apply pending |
| AI | AI mode | TODO | After stability phase |

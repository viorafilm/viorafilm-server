# Sprint Current (S1)

## Sprint Objective
Stabilize production baseline for viorafilm and lock deployment/security path.

## Sprint Tasks
1. Production env hardening:
   - `DEBUG=0`
   - strong `SECRET_KEY`
   - strict `ALLOWED_HOSTS`
2. Verify R2 upload/share flow in production mode.
3. Finalize dashboard parity gap list with concrete tickets.
4. Prepare device authorization gate (design + API contract).

## Definition of Done (Sprint)
- Production env boots cleanly with `manage.py check`.
- Share init/upload/finalize works with R2 presigned links.
- Parity checklist updated with exact remaining deltas.
- Next sprint backlog approved.

## Out of Scope
- AI mode implementation
- Offline 72h lock implementation (design allowed, coding next sprint)

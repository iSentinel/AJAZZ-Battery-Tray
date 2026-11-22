# Resume — individual polling integration candidate

## Verified baseline
- beta.38 PR #50 merged at 6ef83b8d4e9438aca293abf62201d655f0575dea.
- Release workflow 45066102066 PASS; Latest beta.38 published
  2026-11-22T20:24:37Z with six expected assets, verified via gh.
- beta.37 APEX protocol capture published; problem mouse hardware and
  official reference trace still pending. AULA sleep acceptance pending.

## Current work
- Branch feat/per-device-polling: independent validated 15/30/60/120s
  overrides, monotonic completion schedule, actual attempt vs deferred
  discovery, per-receiver measurement timestamps, unchanged HID protocol.
- AULA independent completion-based timer; opt-in and busy/generation
  rules preserved. AULA presence is last-known between its own reads.
- Localized interval editor in tray/dashboard, settings rollback, diagnostic
  interval/timestamp fields, 24 additional pure checks in total.
- Initial PR #51 Windows CI 45066661421 and macOS CI 45066661426 PASS.
- beta.39 version, installer, macOS bundle 43 and release metadata prepared.
- See docs/PER_DEVICE_POLLING.md. Final CI and physical acceptance pending.

## Next
1. Verify final PR #51 CI, merge and six-asset beta.39 publication;
   retain separate physical timing and history/alert acceptance gates.
2. Battery history analytics: estimate observed drain with uncertainty.
3. APEX official reference comparison and AULA physical acceptance when
   hardware becomes available; no speculative HID configuration writes.

Never treat CI as device acceptance. No automatic upload of raw buffers.

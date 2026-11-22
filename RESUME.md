# Resume — beta.40 analytics candidate

## Verified baseline
- beta.39 PR #51 merged at 0d1d13cb99e3aae1726c603ef3cc4d026a3192f1.
- Release workflow 45067421661 PASS; Latest beta.39 published
  2026-11-22T20:38:53Z with six assets, verified via gh.
- APEX problem mouse, AULA sleep and mixed-device timing require physical acceptance.

## Current work
- PR #52 implements local Windows per-device observed discharge rate,
  conditional runtime, sample evidence and observed discharge equivalents.
- Eighteen pure analytics checks; initial Windows CI 45067489196 and macOS
  CI 45067489222 PASS. No new HID traffic or uploaded observations.
- beta.40 version, installer, macOS bundle 44 and release metadata prepared.
- Final CI, publication and physical UI/history acceptance pending.

## Next
1. Verify final PR #52 CI and publish beta.40.
2. Integrate session-only multi-BLE foundation from feat/multi-bluetooth.
   Preserve explicit paired LE consent, fresh GATT trust and conservative
   USB priority. No automatic pairing, persisted identifiers or speculative
   USB/BLE association.
3. Update checker and remaining hardware-gated protocol work.

See docs/BATTERY_ANALYTICS.md for estimate limitations.
Never claim hardware acceptance from CI alone.

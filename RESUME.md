# Resume — Device Manager dashboard (beta.31 candidate)

## Verified baseline
- beta.30 PR #41 merged as bb001b0ed4236dd3ff07f26cc33d7f4d196f9f06.
- Windows/macOS PR and main checks PASS; release workflow 45042853053
  completed successfully and Latest verified v0.3.0-beta.30 with six assets.
- Owner beta.29 confirmed simultaneous independent AJ159/AJ179 reads
  (both 100%, distinct USB revisions), AULA 98% fresh followed by a
  missed reply. Actual icon count, recovery, host sensor preview pending.

## Current work
- Approved expansion roadmap through v1.0.0 saved in docs/ROADMAP.md;
  proposed release milestones retained, but next available beta numbers
  assigned to independently actionable work while hardware gates block.
- Branch feat/device-manager-dashboard-beta31, based on beta.30.
- Roadmap checkpoint 3289ae7132b0c0e89e194f6aa2af2d1eb9a98367.
- Code checkpoint 58ad657436c243a8eeee14caae4a0b2269a4ef06:
  Windows Device Manager read-only dashboard, independent device rows,
  fresh/cached/manual and failure states, local measurement timestamp,
  history/refresh/diagnostics/telemetry controls and EN/RU/UK translations.
  Pure state tests added. No extra hardware polling, no protocol changes.
- L99 wireless screen synchronization remains BLOCKED on exact official
  packet capture, not on implementation of the wired protocol.

## Next
1. [x] Save approved roadmap and verify beta.30 release.
2. [x] Implement initial dashboard and add state tests.
3. [ ] Run PR Windows/macOS CI; review, merge only green and verify six
   release assets. Confirm visible dashboard and all tray icons with owner.
4. [ ] Obtain radio RTC/telemetry frame evidence (docs/AULA_L99_SCREEN_SYNC.md),
   verify framing, checksum, target and weather fields. No speculative writes.
5. [ ] In parallel where evidence permits, implement per-device local aliases,
   independent settings and tray visibility, then battery analytics.
6. [ ] Continue dependency-gated milestones in ROADMAP.md.

Resume by checking actual main/head, open PR and latest CI/release results.
Persist new checkpoints and keep hardware acceptance separate from green CI.
Never export raw device identifiers or claim screen synchronization without
physical confirmation.

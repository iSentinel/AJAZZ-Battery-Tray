# Resume — beta.30 AULA battery recovery

- main baseline ddac018fe8a0c879ae505ced6b9e16c46718f19c, beta.29 Latest
  verified with six assets; PR #40 merged and user installed beta.29.
- Owner report 2026-11-22: independent AJ179 rev 0002 and AJ159 rev 0300
  both F7/05 = 100% at 15:18:18Z. Separate icons setting true, visual
  acceptance pending. AULA 98% at 15:17:48Z then no valid response at
  15:18:19Z while receiver present. Cause not established.
- Working branch feat/aula-battery-recovery-beta30.
- Code checkpoint d922a7dc997b99aa3efb9155df8bd28e86fe66db:
  retry only the existing battery request once; display-only last-good
  cache with expiry on refresh, grey star icon, timestamp, unknown presence
  handling, opt-out generation guard and cache tests. No new HID opcode.

## Next
1. [x] Record owner evidence and implement battery recovery.
2. [ ] Verify beta.30 PR Windows/macOS CI and release; merge only green.
3. [ ] Owner acceptance: AULA fresh reply, transient missed reply/recovery,
   unplug, three visible tray icons; host metrics preview.
4. [ ] Obtain exact official L99 2.4 GHz Instant Data traffic evidence as
   described in docs/AULA_L99_SCREEN_SYNC.md. Wired protocol is not proof
   of radio layout. No automatic or speculative screen writes.
5. [ ] Narrow manual screen telemetry transfer only after evidence, then
   owner screen confirmation and opt-in periodic synchronization.

Inspect main, branch head, latest release and PR/checks before resuming.
No raw private device identifiers or diagnostic files are committed.

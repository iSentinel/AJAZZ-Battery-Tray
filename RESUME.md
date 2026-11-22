# Resume — Windows Device Manager naming (beta.32 candidate)

## Verified baseline
- beta.31 PR #42 merged as 09bc290788ad632f6f4e5d45161f4d8dfa7da9fa.
- Windows/macOS PR and main CI PASS; release workflow 45043535423
  successful; Latest v0.3.0-beta.31 verified with six assets.
- Dashboard visual acceptance and beta.30 AULA recovery remain pending.
- Owner beta.29 independently confirmed AJ159/AJ179 F7/05 100% each;
  L99 returned 98% before a missed reply. Actual screen telemetry
  packet confirmation remains required; no speculative writes.

## Current work
- Branch feat/windows-device-names-beta32 from beta.31 main.
- Roadmap checkpoint ccf8e774493c5f7d09c9ad1c4ed4899087f163a2 adds
  owner-approved standard Windows Device Manager friendly-name work.
- Code checkpoint ea4085917544b26910f42b708a9553db20ea83da adds read-only
  present PnP inventory, exact known USB families and primary HID candidates,
  parent ancestry, current and proposed names, localized scrollable preview,
  and pure identity tests. No property changes, elevation or new HID I/O.
- Revision-based names are provisional. Root/child mapping is not yet
  physically validated; do not infer identity from shared VID/PID.

## Next
1. [ ] Run PR Windows/macOS CI; merge only green; verify beta.32 release.
2. [ ] Owner tests Settings → Windows device names preview with both mice
   and L99; confirm each root/child pair and provisional model.
3. [ ] Implement per-device local aliases; explicit admin-only per-instance
   FriendlyName apply, readback and restore. First back up exact original
   property presence/value. Refuse ambiguous/stale targets or conflicts.
4. [ ] Verify actual standard Windows Device Manager display, restore and
   unplug/replug on physical hardware. Never change drivers or device classes.
5. [ ] Continue individual settings, analytics and other independent
   roadmap milestones while L99 radio screen capture is pending.

References: docs/ROADMAP.md, docs/WINDOWS_DEVICE_NAMES.md,
docs/AULA_L99_SCREEN_SYNC.md.
Resume from actual main/head and PR/CI/release state, not an assumed stage.
Keep private PnP instance IDs local and out of diagnostics and repository.

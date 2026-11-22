# Resume — beta.42 combined candidate

- Latest verified beta.41 (de5079f9), release workflow 45074067608 PASS,
  six assets. Owner AJ179 full diagnostic 6/6 PASS at 100%.
- P0 #53 affected AJ159 remains open. AJ179 GearHub local bridge HAR
  has 266 matching F7 pairs, all 100%; six have nonzero read-ready.
  This is a transport-normalized offline hypothesis, not a live parser fix.
  See docs/APEX_GEARHUB.md. No private raw captures stored.
- PR #54 multi-BLE post-beta.41 Windows 45074388934, macOS 45074388910 PASS.
  Combine PR #56 offline research and eight Python checks in beta.42.
- Session-only BLE, independent retry/alerts/dashboard/icons; pause all BLE
  if any USB receiver present or presence unknown. Underlying WinRT read
  gate held until completion; hung OS operation may require restart.
- Next: final CI and release verification; continue update checker branch.
  Test two paired devices in hardware, collect working and affected AJ159
  full comparison and HAR; retain beta.41 USB protocol until validated.

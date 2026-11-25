# Candidate hardware acceptance — 2026-11-25

Status: NOT RUN on physical hardware. Public beta.60 remains unchanged.
Use exact CI candidates, not GitHub Latest. The integration tree
d5d33138cdd10ceeafc2d28c46fa5853bfb88e05 matches the tested #196
head 3d143a3ff6f4f877b0dc44f9564f114ddfb9c6dc. The latter has hosted
Windows portable run 45568784624, Universal run 45568784656 and High
Sierra run 45568784622. These runs passed. Record the exact downloaded
artifact ID, archive SHA-256, displayed version/build and OS before
testing. A passing CI job is not physical acceptance or trusted signing.
The candidate still displays beta.60 in its version; the commit/build
suffix and archive hash distinguish it from the public release.

## Windows — AJ179 APEX, AJ159 APEX, AULA L99

Close competing vendor utilities; do not change firmware or drivers.
Perform only normal device mode changes and the existing consented
diagnostic read. Keep a working wired input device available.

| ID | Procedure | Required observable result |
|---|---|---|
| W01 | Start with USB receiver connected | Verified percent or explicit unknown; unverified raw HID field never displayed as charge |
| W02 | Pair mouse; Bluetooth inspector > Read selected battery | Fresh GATT 2A19 explicitly identified, not Windows cache |
| W03 | Enable selected BLE monitor (remember on this PC) | Automatic direct GATT continues while USB receiver remains inserted |
| W04 | Restart application with Bluetooth mouse awake | Previously opted-in endpoint restored, no historical percentage before fresh GATT |
| W05 | Restart while endpoint unavailable, then reconnect | Pending saved consent can recover; unrelated endpoints are not auto-enabled |
| W06 | Let mouse sleep; inspect after failed read or 120 seconds | Last direct value marked cached, not fresh; no new alert from cache |
| W07 | Wait 30 minutes from last direct success without any new successful read | Cached value expires, no false zero |
| W08 | Wake; Refresh Bluetooth battery now | Fresh GATT replaces cache; failures reset after successful reply |
| W09 | In Opted-in BLE devices > Link to USB receiver, confirm same mouse | Exactly one logical tray presentation for linked pair; no automatic identity matching |
| W10 | Switch BLE / 2.4 GHz with receiver inserted, then remove/reinsert receiver | Linked icon remains; validated USB first, fresh GATT next, marked cache or unknown otherwise |
| W11 | Attach an unrelated receiver with multiple icons enabled | Linked primary stays stable if already selected; unrelated devices stay separate |
| W12 | Unlink; repeat with one icon and multiple icons | Separate presentation restored; no false charge or unrelated history merge |
| W13 | Disable saved monitor during read; restart | No late reply restores consent; no auto-monitor after restart if save succeeded |
| W14 | Enable AULA monitoring; sleep and wake normally | Last-good cache is marked, fresh reply restores value; no false zero |
| W15 | Start diagnostics session; capture baseline, switch/wake markers | Count advances, passive markers do not issue extra HID queries |
| W16 | Collect full diagnostics with explicit consent; review and add | Reviewed report included only on explicit action |
| W17 | Save ZIP after two or more snapshots; try existing destination | Valid local archive, existing file unchanged, failed save retains session |
| W18 | Discard session or exit and restart | In-memory snapshots cleared; exported file remains local |

A cached scheduled USB sample may be used for linked display up to
three minutes and must be marked cached. Low-battery alerts are based
on validated readings only; USB and BLE history/alerts remain separate.
If opt-out save fails, expect a warning that monitoring may resume
after restart; do not mark W13 passed in that case.

## macOS — repeat separately on Universal and High Sierra

Universal requires macOS 13 or later; High Sierra targets Intel
10.13, including the iMac Late 2013 with 10.13.6. Hosted native tests
run on a newer Intel macOS, not the actual 10.13 system.

| ID | Procedure | Required observable result |
|---|---|---|
| M01 | Launch the edition on target OS | Menu bar app launches without dyld/availability errors |
| M02 | Device diagnostics / Copy diagnostic report | Passive snapshot, no extra device request; correct edition and build |
| M03 | Run HID diagnostics with consent | Bounded F7/05 report; UI stays responsive; no unverified charge promotion |
| M04 | Cancel active diagnostic | Incomplete/cancelled report does not claim fresh charge |
| M05 | Start session; capture baseline and transport/sleep/wake marks | Counts increase, no new device I/O; wait a second between captures |
| M06 | Review active diagnostic; explicitly add report | Report added, marker is ReviewedReport, not a detected event |
| M07 | Save local ZIP and attempt existing target | Valid archive, private mode 0600, existing file not overwritten |
| M08 | Discard session or quit | Memory-only collection cleared; no automatic upload |
| M09 | Manual Bluetooth inspector if paired device supported | Fresh direct GATT or explicit failure; no automatic persistent BLE on Apple |
| M10 | Switch EN/RU/UK; reopen session menu | Correct labels, current count and retained session |
| M11 | Sleep/wake and unplug/replug | App remains responsive; no false zero or false disconnect from unknown presence |

## Reporting and decision

Report PASS, FAIL or NOT RUN per ID, separately by platform and edition.
For each failure include expected vs observed behavior and a redacted
report, without serial numbers, device addresses, raw buffers or private
paths. ZIP may contain explicitly authorized reply bytes; review locally.

The reviewer can analyze a session with:

```sh
python3 tools/compare_diagnostic_timeline.py --session session.zip
```

A successful parse does not establish physical device identity, prove
freshness of historical observations, or imply any scenario passed.
Record exact candidate provenance and actual human observations.
No hardware tests are marked passed by this document. The release hold
remains until required acceptance, exact artifacts and admission gates
are reviewed.

## Exact Apple artifact static verification

CI #196 artifacts fetched by exact ID; outer SHA-256 matched the GitHub
REST digest and inner ZIP SHA-256 matched its companion checksum file.

| Edition | Artifact ID | Inner ZIP SHA-256 |
|---|---:|---|
| universal | 15001581433 | `7795dc68af28cc1fe905ffe1a0d6d05141366f80cb62e89302c0216614acd676` |
| high-sierra | 15001876157 | `a280edf68cf54ddac6946d71ec3b14e71c287b98585851987da836a1d71fa4c3` |

Both: archive layout, direct Mach-O load commands, undefined-symbol
inventory, scoped ad-hoc code/resource hashes and scoped SBOM PASS.
High Sierra SDK name screen: 159 imports; 154 unrestricted
name matches (90 direct), 5 restricted-only, 0 missing.
The five restricted-only names are reachable through the AppKit reexport
chain. Linker directive semantics, mirror trust, actual 10.13 symbol
availability, notarization and signer trust are NOT VERIFIED.
Static evidence remains separate from physical acceptance.

SDK screen JSON SHA-256: `6b8547e3e495213da2c7450369cebc7ecd771725cad45bb57807f6fa8edfd179`.

## Exact Windows portable candidate static verification

Artifact 15001321555 from run 45568784624 (head 3d143a3):
outer ZIP SHA-256
`6d8ce9f20d08f60445ef69e765631c212ea6c37dfd40a0cca84225718b5d9c68`
matches the GitHub REST digest. The EXE is 149610595 bytes, SHA-256
`3d96f335de50fa3e63bb6092424745b361f5f46e0bbd55f479658c282a3f38e0`.
Four shortcut ICOs match the source bytes. Bundle inventory, scoped
dependency attribution, host sections, resource payloads, conditional
header reconstruction and resource serialization all passed using the
previously pinned NuGet packs. The scoped Windows CycloneDX 1.6 BOM
contains 269 components (including four package components), with
all three candidate BOMs passing the local CycloneDX 1.6 schema.
The Windows EXE certificate table is absent. No Authenticode trust,
complete distribution SBOM, redistribution approval or physical
acceptance is established.

The prior installer CI tested an unpublished beta.61 upgrade and a
separate synthetic beta.62 lifecycle probe but retained no installer
artifact. The updated workflow preserves the verified beta.61 setup
before the probe rebuild and uploads only after all tests pass, with
source and setup/app SHA-256 metadata. This is a short-lived CI
artifact, not a release. The new artifact must be checked after CI.

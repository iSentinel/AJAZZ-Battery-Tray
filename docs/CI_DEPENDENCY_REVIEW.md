# CI dependency review — ENG-06

Source baseline 17a65b8 (merged #140). 26 external action uses across
nine workflows now pinned to five full upstream commit SHAs. Lock inventory:
config/ci-actions-lock.json. The four active action SHAs were observed in
successful hosted run logs 45517044816 and 45517044867, also consistent
with macOS, High Sierra, HA preview and upgrade logs. The held release-only
download-artifact v4 SHA was resolved directly from the upstream GitHub
tag ref; it has not been executed for this candidate. All five commit
identities were confirmed with the official upstream repository API.
This is identity/compatibility evidence, not a full source/advisory review.
No major/minor action bump selected. Python 3.12.16 matches prior hosted
QA evidence. All twelve workflow jobs have explicit finite timeouts
(existing limits retained; new 15/20-minute limits based on observed runs).
Offline regression checks exact reviewed refs and job budgets in the
repository's current canonical block YAML style. They are not a general
YAML parser or protection against a malicious workflow editor.
Workflow/config changes trigger offline QA. Do not weaken the release hold.

Outstanding: .NET exact SDK/runtime and NuGet resolved graph, hosted image
revision, Xcode/Swift/Clang, Inno Setup (observed 6.7.1), reproducibility,
action transitive dependencies, notices/licenses, SBOM, advisories and
disposition. No unreviewed tool upgrades, release dispatch or live
production mutation. Native and hosted QA required for this candidate.

## SDK selection follow-up (separate candidate)

Windows 45517112616 and installer 45517112819 logs report setup-dotnet
found SDK 8.0.428 already installed. They do not establish the selected
SDK when a newer SDK is present. This follow-up adds global.json
(version 8.0.428, rollForward disable, no prerelease) plus matching exact
setup-dotnet input and selected SDK verification in all four jobs.
This is an explicit selection change that requires native regression,
not a claim of identical prior compiler output. Developer builds now
require the exact installed SDK. Installed runtime version inventory
and Apple Xcode/Swift/Clang/SDK observation steps added; neither locks
the resolved runtime/NuGet graph or Apple runner image. No path or
credential intentionally emitted in the new Windows inventory.
Inno 6.7.1 observed in prior upgrade logs; installer fallback still
requires a separate supply-chain review. No new package downloads
or installer changes here. Node 20 actions forced to Node 24 warning
in earlier CI is recorded for review; no automatic action upgrade.

## Owner-selected .NET 11 migration (2026-11-25)

#143 merged 48b1fff, six hosted checks passed, identical tested tree.
Owner explicitly selects .NET 11 rather than .NET 10. Microsoft lists
11.0 GA, SDK 11.0.100, runtime 11.0.0, released 2026-11-10, supported
through 2028-11-14 (STS): https://dotnet.microsoft.com/en-us/download/dotnet/11.0
and https://dotnet.microsoft.com/en-us/platform/support/policy.
This candidate changes SDK/TFMs and CI, not device protocol. Windows API
target is retained provisionally; it is not an OS support guarantee.
Review breaking changes, actual resolved runtime and installer/native
behavior before admission. Local QA not executed; hosted checks pending.
No release dispatch. See #144 and #142.

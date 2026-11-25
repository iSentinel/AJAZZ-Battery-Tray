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

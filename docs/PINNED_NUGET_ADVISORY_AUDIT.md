# Scoped pinned NuGet advisory audit — ENG-12

The offline CLI checks the four exact stable package versions from the
pinned license inventory against both pages of the reviewed NuGet.org
VulnerabilityInfo snapshot. It supports the observed interval grammar,
including inclusive/exclusive bounds, prerelease boundaries and four-part
versions. Unsupported ranges, malformed data, duplicate JSON keys or missing
pages fail closed. No third-party service is contacted by the CLI.

```sh
python tools/audit_pinned_nuget_advisories.py --snapshot /path/to/snapshot --output advisory-audit.json
```

Use a fresh directory with index.json and its base.json/update.json pages
retrieved from the HTTPS service index, preserving exact page identities.
The observed official index is https://api.nuget.org/v3/vulnerabilities/index.json.
The CLI records input hashes, page URLs and update times; these do not prove
page authentication, completeness, freshness or release admission. Exit 0
means no matching ranges in the supplied snapshot; exit 2 means a match or
an invalid/incomplete input. A fresh authenticated acquisition and policy
review must precede release admission.

## Actual observation — 2026-11-25 UTC

| Package | Version | Examined ranges | Matching ranges | OSV returned IDs |
|---|---|---:|---:|---:|
| Microsoft.NETCore.App.Host.win-x64 | 11.0.0 | 1 | 0 | 0 |
| Microsoft.NETCore.App.Runtime.win-x64 | 11.0.0 | 130 | 0 | 0 |
| Microsoft.WindowsDesktop.App.Runtime.win-x64 | 11.0.0 | 80 | 0 | 0 |
| Microsoft.Windows.SDK.NET.Ref | 10.0.19041.87 | 0 | 0 | 0 |

Base updated 2026-11-20T05:34:20.7684268Z; update page updated
2026-11-24T11:34:46.1586875Z. SHA256 of decoded input JSON:

- index: e9411ec933b7f63fa2e4c5fd68e1c0031ee6928f289006dc6a3c0d1c6610203a
- base: 1eb8e70c6f384340d6033fc3c48fd9e5dbc5750d1dcd00d1463df4385637ae9a
- update: 4bea167a58dcd05bff4210a96618a9b284267c77f9159655582fb6879ee8d302

OSV exact NuGet package/version POST queries returned no advisory IDs or
pagination tokens for all four. This is a cross-check, not necessarily
independent underlying advisory coverage. No match for the SDK is not a
claim that its underlying Windows APIs have no vulnerabilities. Toolchain,
Inno Setup, Apple system components, SDK product-level security advisories,
all other dependencies and exact release artifacts are not covered.
Six synthetic regressions exercise boundaries, missing pages, duplicate
keys and matching advisories. Release hold remains unchanged.

References:
- https://learn.microsoft.com/en-us/nuget/api/vulnerability-info
- https://learn.microsoft.com/en-us/nuget/concepts/auditing-packages
- https://google.github.io/osv.dev/post-v1-query/

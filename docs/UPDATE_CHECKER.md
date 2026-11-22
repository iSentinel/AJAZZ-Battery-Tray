# Windows update checker — foundation

## Channel rules
- Stable: actual stable tags only, excluding drafts and GitHub prereleases.
- Experimental: stable releases and strict beta tags; the beta tag determines
  the channel regardless of GitHub prerelease=false (our beta releases are Latest).
- Compare numeric major/minor/patch and beta suffix; stable beats beta of
  the same base. Never offer the current or an older version.
- Require exact artifact name and single SHA-256 entry. A checksum detects
  corruption; it is not an independent publisher signature.

## Implemented manual lookup
- Fixed GitHub API requests, no authentication or cookies, no redirects.
- Overall 15-second cancellation deadline, 2 MiB response limit, first 100 releases.
- Explicit tray dialog, EN/RU/UK, session channel selector and release-page link.
- No automatic check, download, installer execution, or use of remote URL fields.
- 26 pure version/checksum/metadata checks; CI pending. HTTP errors are shown
  generically; live network and UI acceptance pending.

## Remaining integration
- Explicit manual check first; optional periodic checks disabled by default.
- Fixed GitHub repository API, HTTPS, bounded response and timeouts, no tokens.
- Verify exact known Windows artifact name, release tag and download URL.
- Show version, selected channel and release page; do not execute installers
  automatically. Download/verification and installation are separate actions.
- Do not expose device telemetry, settings, hardware IDs or local paths.
- Tests for rate limiting, HTTP failure, malformed metadata and invalid links;
  actual UI and network acceptance remain outstanding.

## Local artifact verification (next beta)
- Explicit tray command **Verify downloaded release...**; choose the original
  Windows setup or portable EXE and its companion .sha256 file from the same
  GitHub release. Renamed files are rejected; selecting another EXE clears
  the chosen manifest. No automatic file lookup or downloaded code execution.
- Read-only local streams, bounded 512 MiB artifact and 1024-byte ASCII
  manifest, strict artifact/manifest names, single matching hash entry,
  asynchronous cancellable SHA-256 computation. No network request.
- A matching hash proves equality with the selected manifest only, not
  release authenticity, a signature, or that both files came from GitHub.
  The user must obtain the manifest from the intended release independently.
- Twelve local synthetic-file regression cases; Windows CI and physical
  dialog acceptance pending. Automatic release notifications remain a
  separate opt-in feature.

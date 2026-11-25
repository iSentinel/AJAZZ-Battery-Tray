# Inno publisher evidence — ENG-06/12

On 2026-11-25 the publisher's verification instructions
(https://jrsoftware.org/inno-setup/downloads/verify) identified
Pyrsys B.V. for Authenticode and both ISSig key download channels.

Fetched both public key files directly from
https://files.jrsoftware.org/is/misc/ using HTTPS with normal
certificate verification, HTTP 200, curl SSL verify result 0,
and no redirects. Compared exact bytes to the source-tag copies:

| Key | SHA-256 |
| --- | --- |
| def01.ispublickey | 3b0b7e1e478c9ab327746a990512e2b245c9231e88a7fdd60d7874dd439db562 |
| def02.ispublickey | 32bea6bceb4ac7c4e6b3becdf3fb38de77378c5e76d494ab907d87cfab9e597b |

Both match. The existing OpenSSL ISSig verifier replayed all 18
signatures with the independently fetched key files, 18/18 valid
for those pinned keys (11 def01, seven def02). Evidence SHA-256
f70f2e72f6362fc7affc69e14f3b7091f637821448c2b3228c0c306e8ed106d0.
This corroborates the published key bytes via two HTTPS channels;
it does not establish an independently audited historical key
rotation, revocation or PKI policy.

GitHub release is-6_7_1 REST metadata reports immutable=true,
published 2026-02-17, asset 357294783, SHA-256
4d11e8050b6185e0d49bd9e8cc661a7a59f44959a621d31d11033124c4e8a7b0,
10619024 bytes; signature asset 357294875, SHA-256
09ea9b9931a562cae199fecd76583cab22d0a50506912d211a5cfb2fe4ebf2c5.
Both local digests match. REST metadata is not attestation verification.

The local Debian GitHub CLI 2.46.0 lacks release verify-asset.
Add a separate CI-only read-only Windows job which downloads the
exact official asset, checks size/digest, validates native
Authenticode, embedded signature type, expected publisher and
timestamp certificate presence, then requires successful
gh release verify-asset against the specific public upstream tag.
No installer execution, release dispatch, privilege change, or
binary upload. Only JSON evidence is uploaded; hosted verification
is pending. Native trust is scoped to the runner's trust store
and observation time. The AJAZZ candidate remains unsigned and
release admission remains blocked.

References:
- https://jrsoftware.org/inno-setup/downloads/verify
- https://github.com/jrsoftware/issrc/releases/tag/is-6_7_1
- https://cli.github.com/manual/gh_release_verify-asset
- https://learn.microsoft.com/powershell/module/microsoft.powershell.security/get-authenticodesignature

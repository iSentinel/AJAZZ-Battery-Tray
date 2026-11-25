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

## Native CI result — 2026-11-25

PR #220 exact head df95dab6dee7bb049f50ce93898ca86597cd2f2d,
run 45596849671, job 139145066333: PASS. Evidence artifact 15013306813,
ZIP SHA-256 3e74914c736f544708cf602902e21fc0d969472503c4427b04e6af03c5611e9a
matches REST digest; exactly authenticode.json and release-attestation.json.

Native Authenticode Valid, embedded Authenticode, publisher Pyrsys B.V.,
issuer Sectigo Public Code Signing CA R36, signer certificate SHA-256
4efd84e6f1091b19321231743b9aa86482effd6d0bea9f7a44db6211154616f3.
Timestamp certificate present, SHA-256
a1275b9c448e09844a9c729d623ae5718d84733e0477b86a451895c5fe909ead.
GitHub release verification succeeded; verified identity
https://dotcom.releases.github.com, Fulcio Intermediate l1,
timestamp 2026-02-17T11:31:00Z. Verified statement names repository
jrsoftware/issrc, tag is-6_7_1 and both exact EXE and ISSig hashes
listed above. This is upstream release asset trust evidence on
the hosted runner, not an independent reproduction of the compiler
or trust/signature admission for the AJAZZ candidate.

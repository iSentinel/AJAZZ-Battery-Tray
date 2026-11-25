# .NET notice staging and redistribution review — ENG-06/12

Local-only staging preserves the exact root notice bytes from the four pinned
packs in the license inventory. A fresh output directory contains package
subdirectories and a manifest with lengths and SHA-256 values. The Windows SDK
subdirectory has no notice files because none were observed in its package.
All inputs are validated before output creation; incomplete directories from
I/O failures are not valid evidence and must not be reused. No distribution
or release workflow is changed.

```sh
python tools/stage_dotnet_notices.py --host host.nupkg --core core.nupkg --desktop desktop.nupkg --sdk sdk.nupkg --output staged-notices
```

Real pack test: five files staged, all five re-read with exact matching
length and SHA-256. Three synthetic regressions cover byte preservation,
invalid inputs and no replacement. The manifest is not legal clearance.

## Redistribution findings — 2026-11-25

- The inspected Windows SDK Ref 10.0.19041.87 pack supplies two embedded
  assemblies from lib/net9.0: Microsoft.Windows.SDK.NET.dll and WinRT.Runtime.dll.
  Both matched the pinned pack in the earlier provenance audit.
- Microsoft Windows SDK license section 2a and official REDIST.TXT list
  include a dedicated Microsoft.Windows.SDK.NET.Ref section. The list
  describes unmodified package/program distribution for WinRT API use,
  but its explicit paths refer to net8.0 and net6.0, not the observed
  net9.0 paths. Do not conclude either unrestricted permission or prohibition
  from this discrepancy; exact version coverage and conditions need review.
- .NET's Windows licensing information distinguishes the MIT source/package
  declaration from product redistribution terms for single-file runtimes.
  Review the .NET Library License and other applicable component terms,
  including downstream terms; the MIT nuspec alone is insufficient.
- Existing portable EXE and installer must ultimately carry applicable
  notices and terms, with a reviewed distribution design and explicit
  candidate-bound admission. Do not publish incomplete license material.

References:
- https://learn.microsoft.com/en-us/legal/windows-sdk/license
- https://learn.microsoft.com/en-us/legal/windows-sdk/redist (2024-10-21 list)
- https://github.com/dotnet/core/blob/main/license-information-windows.md
- https://github.com/dotnet/core/blob/main/license-information.md
- https://dotnet.microsoft.com/en-us/dotnet_library_license.htm

No license acceptance on behalf of the owner, legal conclusion, trusted
signature validation, SBOM completion or release admission is asserted.

## Historical #206 exact application SBOM replay

The application recovered from the previously qualified #206 setup
has SHA-256
429613466f2e44d8f65d80d4e77c3532d59b6c72e4bc9f613c7faa86ff9dd955.
The existing scoped Windows SBOM builder ran on these exact bytes
and all four retained hash-pinned packs. Host sections and reconstructed
resource comparison passed, and the builder matched all 265 bundle
files to the project/configuration or reviewed packages (179 core,
81 desktop including 52 localized resources, two SDK, three project
and configuration files). Four source-pack library components are
included; total 269 components, composition explicitly incomplete.
SBOM SHA-256
8b265767820c7fd26e037c982f3c338eded810b35d67c5d023e705bb12e4d50d.
This replay is specific to #206, not the distinct #228 product-probe
binary. Independent schema validation was not repeated in this replay;
dependency graph, advisories, signatures and release admission remain
unverified.

The two SDK assembly observations match the exact reviewed package:
Microsoft.Windows.SDK.NET.dll SHA-256
4ea9a22cfa51aa90d57196b51bd3710da0e6dd7142251d041bc66b40188d081c;
WinRT.Runtime.dll SHA-256
42ac514d4aecdd3137b5f6513270de8082af81d9f205a62b7379f0f3f229319c.
No standalone entries named coreclr.dll or the WPF-specific DLLs
listed in the Windows license guidance were found in the bundle
manifest; this does not exclude native runtime code in the host.

Rechecked Microsoft's Windows license guidance and .NET Library
License section 3(a) on 2026-11-25. Product single-file runtime terms
and downstream distributor/end-user protections are distinct from
the package MIT metadata. Section 3(a) also imposes conditions on
distribution, including indemnity; section 4 addresses data.
The Windows SDK REDIST list still identifies the reviewed October
2024 version. Exact SDK net9.0 coverage, downstream terms, privacy
assessment and complete notices need owner/legal review. Technical
notice transport success is not acceptance of license terms.

## Candidate-bound product notice SBOM

The separate hosted product notice workflow now invokes
`build_product_notice_sbom.py` after clean, upgrade and repair
lifecycle verification. It requires exact app, setup and checkout
hashes in both lifecycle records, builds a scoped CycloneDX 1.6 BOM
from the actual published-by-CI EXE and four pinned packages, and
checks the root application digest. A separate binding records exact
BOM bytes and both lifecycle document digests. Only JSON artifacts
are retained. Composition is explicitly incomplete; independent
schema validation, advisories, distribution compliance, physical
acceptance and release admission remain unverified. Native CI pending.

## Independent local CycloneDX validation

The exact retained #206 BOM (SHA-256
8b265767820c7fd26e037c982f3c338eded810b35d67c5d023e705bb12e4d50d)
passed independent Draft7 validation against the three retained
hash-pinned CycloneDX schemas. The optional local validator dependency
lock is scoped to Linux x86_64 CPython 3.13; six exact wheels were
verified against PyPI file SHA-256 metadata and installed in an isolated
virtual environment using --require-hashes and --no-index. No system
Python changes. The CLI validates with a local registry and never
retrieves remote schema references. No claim of publisher signature
verification for validator packages or of full SBOM coverage.

```sh
python -m venv .venv-sbom
.venv-sbom/bin/python -m pip install --only-binary=:all: --require-hashes -r config/sbom-schema-linux-cp313.txt
.venv-sbom/bin/python tools/validate_scoped_sbom_schema.py --sbom sbom.json --schema-dir cdx-schema --output schema-evidence.json
```

Use the three reviewed local schema files whose hashes are pinned in
the verifier. For the new product-probe BOM also supply --binding
product-sbom-binding.json. Actual historical schema evidence SHA-256
667623b4bd919c04efcc028a7b55c49b7d1cdd885c98f9a4d99dad3bb10a7d23.
The new product BOM still requires exact native evidence.

## Native product probe SBOM and scoped advisory replay

PR #230 exact head 533c787d97669ef822b780d756af3dc273254ad5,
hosted checkout b75f0e07a242f22317821c9007d9f4def067620f,
run 45626121143, job 139246657930: PASS.
Downloaded three evidence ZIPs; their SHA-256 digests match REST:
- SBOM artifact 15028403507:
  a6b76244e475a47b4e4d673ead188c65a9f5ea1aa47fee43ac8683bcb773e206
- Clean artifact 15028142667:
  e1d66e4014c30e26523190fd65f598b2ba51d2567980a894ca8492c212514502
- Upgrade artifact 15028103439:
  789468aa14469ea06140b9173c8b8bb80c80508fb0b131b16630f7e7360b8d33

The raw clean/upgrade lifecycle document hashes match the BOM binding.
Source, app and setup identity agree across the three records.
App SHA-256 2be82a40ef1c42fca007683e03c50e3ddb6132b8e329e94bf0f2f80ea29943ff;
setup SHA-256 7871c7f274da2197886e57fdf2bceac3d82f82ae0a24f5aed5b0ab2a559d93c9.
269 components, BOM SHA-256
a54d607827ad11c171a5b6fc2689a61b728b7ee1362b8e220941149a48f8bc59.
Independent local CycloneDX Draft7 schema validation with candidate
binding PASS; evidence SHA-256
7e2c735e716bedaff76df91b2a08fdb150d85e7e233c03df7f2acb5e799dd8d5.

NuGet VulnerabilityInfo acquired over certificate-validated HTTPS
on 2026-11-25. Initial reads returned gzip and inconsistent index
observations; the successful bounded retry obtained identical
index bytes before/after page acquisition. Base updated
2026-11-20T05:34:20.7684268Z, update
2026-11-25T05:34:51.2524425Z. Index SHA-256
af1d2487d01953fd5605b58d58a89a440fdca823ba7b370f635f30edc5ff8055.
Base and update page digests match the earlier snapshot; 211 ranges
examined (host 1, core 130, desktop 80, SDK 0), no matching ranges.
The candidate-bound audit verifies the exact four source pack
identities, package digests, PURLs, schema evidence and BOM identity.
Actual advisory evidence SHA-256
f58f61edb38b9e45fe910b7d364dbcac56027af3e4cbdb591954c95d17dfd5e4.
This is a dated snapshot observation, not an authenticated signed feed,
freshness gate, complete dependency graph, absence of vulnerabilities,
or release admission. Installer, Apple, OS and other advisory
coverage, license terms and physical acceptance remain open.

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

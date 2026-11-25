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

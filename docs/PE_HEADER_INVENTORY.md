# Scoped PE header inventory — ENG-12

Independent follow-up to the verified #155 resource payload overlay. The
offline tool compares the pinned .NET 11 x64 host template against the
candidate single-file EXE. It reads only local bounded files; does not execute
the EXE or extract resources. The exact host package and template hashes are
enforced by the existing host verifier.

```sh
python tools/inventory_dotnet_host_headers.py --exe AJAZZBatteryTray.exe --package host.nupkg --application tray --output headers.json
python tools/inventory_dotnet_host_headers.py --exe AjazzHaPreview.exe --package host.nupkg --application ha --output ha-headers.json
```

The inventory compares COFF and PE32+ optional fields, the sixteen data
directories, section order and complete section-table metadata, and hashes
of DOS stub and header padding. It rejects unsupported structures, truncated
fields, overlapping raw section ranges, and invalid certificate-table extents.
Selected invariants and expected Windows/console subsystem are checked.
All other differences are reported for review; they are not silently allowed.

Exit 0 means only the selected invariants match; exit 2 means a structural
or invariant failure or inability to produce a new report. Output is
no-replace JSON. A present certificate table is not a valid signature.
The tool does not validate resource metadata, section padding outside the
header, signatures, arbitrary directory RVA semantics, or explain all SDK
header mutations. Header equivalence remains NOT_VERIFIED.

Six synthetic regressions and common QA CLI integration added. Native
artifacts and pinned template must still be compared on exact reviewed
inputs; no actual artifact PASS claimed at this checkpoint. Release hold
and hardware state unchanged.

# High Sierra SDK name screening — ENG-12

This is a preliminary static comparison, not a native compatibility test.
The inputs are third-party mirror SDK text stubs, not installed system
binaries, and are not an authenticated Apple SDK distribution. No SDK
files are redistributed in this repository.

## Bound inputs

- Source mirror: https://github.com/phracker/MacOSX-SDKs
- Mirror commit: 041600eda65c6a668f66cb7d56b7d1da3e8bcc93
- SDK: MacOSX10.13.sdk, x86_64, text stub v2.
- Evidence manifest SHA-256:
  ad6ec14c1751aded035b124f4711c2c34455da183912edbbdec1ec727f73b2ce
- Actual High Sierra app ZIP from integrated 7c25cfa, artifact 14995547596:
  4bcb70b5ae3caed520f54753c48f4700f914e9ef14019841b6477ccacf9b028c
- Local replay output SHA-256:
  ae5434d313e306a24593c0319d1bd153392981029872b0c303165fe1cdfa2c04

65 content-addressed local stubs, each verified against the manifest,
and 62 recorded reexport edges. The original mirror acquisition is not
a trust clearance. The offline CLI requires independently supplied
archive and manifest digests, recomputes the High Sierra symbol inventory,
validates the architecture, install names, stub digests and graph edges,
and rejects missing or unrelated nodes. Optional PyYAML is required for
actual text stub parsing; the core regressions require only stdlib.
The CLI never downloads or installs a dependency.

    python tools/screen_high_sierra_sdk.py --archive app.zip --sha256 SHA256 --manifest manifest.json --manifest-sha256 SHA256 --stub-dir stubs --output screen.json

## Measured results

| Imported library | Imports | Direct unrestricted names | Unrestricted graph name matches | Restricted only | Missing names |
| --- | ---: | ---: | ---: | ---: | ---: |
| AppKit | 19 | 14 | 14 | 5 | 0 |
| CoreBluetooth | 2 | 2 | 2 | 0 | 0 |
| CoreFoundation | 17 | 17 | 17 | 0 | 0 |
| Foundation | 16 | 16 | 16 | 0 | 0 |
| IOKit | 10 | 10 | 10 | 0 | 0 |
| libSystem | 49 | 0 | 49 | 0 | 0 |
| libobjc | 26 | 26 | 26 | 0 | 0 |
| Total | 139 | 85 | 134 | 5 | 0 |

All five restricted-only names are attributed to UIFoundation in the
reviewed AppKit reexport graph. The corresponding export group lists
AppKit as an allowable client. Names: NSFontAttributeName,
NSForegroundColorAttributeName, NSParagraphStyleAttributeName,
NSFont class and NSMutableParagraphStyle class. This is not evidence
that the application illegally links a private framework: its declared
dependency is AppKit. The conservative screen does not evaluate
client authorization or reexport linker semantics. 19 relevant
deployment-related linker directive records are retained for later review;
the CLI does not interpret them.

All 139 names occur somewhere in the SDK graph; 134 have an unrestricted
name candidate. Neither figure establishes actual availability, a working
dyld binding, OS export provenance, Objective-C selectors, runtime
dynamic API compatibility, native launch, signing or release admission.
Next: review the five client constraints and linker directives, then
collect authenticated OS export and native hardware evidence.

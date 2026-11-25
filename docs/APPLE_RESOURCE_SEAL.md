# Scoped Apple ad-hoc resource and CodeDirectory integrity — ENG-12

The offline tool requires an externally supplied expected ZIP SHA-256,
the exact reviewed app layout, and valid Mach-O slice bounds. It checks
both SHA-1 and SHA-256 entries for the four resource icons against the
actual ZIP bytes, then validates the reviewed LC_CODE_SIGNATURE extent,
three-slot superblob, zero tail, SHA-256 ad-hoc CodeDirectory v20400,
bundle identifier, every 4 KiB code page (including the partial final
page), and three special slots: Info.plist, empty Requirements, and
CodeResources. Only the observed empty CMS wrapper is accepted. It is
not a general-purpose Apple signature verifier or resource rule evaluator.

```sh
python tools/verify_apple_resource_seal.py --archive app.zip --sha256 SHA256 --edition universal --output seal.json
```

Actual historical e00b229 artifacts from #168, previously outer/inner
hash-qualified, both exited 0:

| Edition / slice | Covered bytes | Code pages | Special slots |
|---|---:|---:|---:|
| Universal x86_64 | 392736 | 96 | 3 |
| Universal arm64 | 408640 | 100 | 3 |
| High Sierra x86_64 | 102096 | 25 | 3 |

221 code page hashes, nine special-slot hashes and 16 resource hashes
(eight per archive) matched. All signatures have flags 2 (ad hoc), an
empty CMS wrapper and empty Requirements. No signer identity, certificate
chain, trusted timestamp, notarization, complete CodeDirectory semantic
validation, native codesign acceptance or runtime compatibility inferred.
The checked resource entries do not establish general rule semantics.
A re-signed archive could pass local hash consistency; provenance depends
on independent expected archive identity. Six synthetic regressions cover
resource/covered-byte tampering, slot changes and malformed signature
metadata. Exact hosted CI and native acceptance remain required.

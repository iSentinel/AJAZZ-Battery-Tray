# Resume — offline resource comparison and AULA acceptance

- beta.51 PR #65 final Windows 45090441648 / macOS 45090441628 PASS;
  merged a1d9a06e61e11248e69d9746b29bc8699314e2c3.
  Release workflow 45091032358 started; confirm all six assets.
- PR #66 test/resource-comparison synced with beta.51 main; RESUME
  conflict resolved. No runtime, installer, macOS or release code changes.
  23 offline Python tests PASS on Gateway. Dedicated Python CI pending.
- Passive AULA sleep/wake acceptance document includes 12 scenarios,
  no forced refresh during sleep, privacy-safe copied summaries, explicit
  NOT RUN/NOT OBSERVED rather than fabricated hardware results.
- Next: verify beta.51 publication and exact PR #66 head CI; merge tools
  after PASS without unnecessary application version bump. Review other
  independent roadmap work while awaiting actual Windows measurements.
- Physical AULA sleep/wake, both AJ159 reports/HAR, multi-BLE and actual
  Windows resource comparison remain outstanding; HA optional.

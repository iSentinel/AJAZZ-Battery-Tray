# Inno Setup toolchain selection — ENG-06/12

The integrated #99 upgrade run 45548252489 reported the Windows
2025 VS2026 hosted image and engine 6.7.1 for both beta.61 and synthetic
beta.62 installer compiles. Previously the workflows selected the first
ISCC found and silently installed a floating Chocolatey version if absent.
Replace that fallback with a common preinstalled-compiler wrapper; require
exactly one compiler at the reviewed Program Files locations, successful
compilation, exact engine banner 6.7.1 and fresh output. Frontend file
version is recorded as an observation only.
Record SHA-256 of the compiler and Setup and Authenticode status as an
observation only. No compiler download, installation, signer trust decision,
version upgrade or release admission is performed. A runner image update
that removes the compiler or changes its version intentionally blocks the job.

```powershell
# After dotnet publish into dist/app; creates a Setup, not a dry-run.
.\tools\Invoke-InstallerCompiler.ps1
# CI-only fixture; not a release command.
.\tools\Invoke-InstallerCompiler.ps1 -AppVersion 0.3.0-beta.61
```

Release workflow remains explicitly held. No compilation or native
PowerShell execution on Gateway (pwsh absent); hosted installer CI must
verify the exact engine banner and observed frontend metadata, both
upgrade cases and ordinary release-path wrapper invocation before release.
Three local source contract tests cover shared selection, probe isolation and
release hold, not actual compiler trust.

## License review (2026-11-25)

Reviewed Inno Setup upstream tag `is-6_7_1`, annotated tag object
`484a38a681f41ced5f8f0eb9890f7932ca6a244c`, license.txt SHA256
`2e5346868c2a18434489824e11d65c3031620f792fefc415d05f19cd441abf5c`.
The source license permits commercial use subject to retention of notices
and other conditions; the author separately requests commercial users
purchase a license. No assumption of project commercial status or purchase.
Review generated Setup/uninstaller embedded notices and bundled components
(LZMA, other libraries), exact toolchain provenance and applicable advisories
before redistribution. No legal or license acceptance conclusion.

References:
- https://github.com/jrsoftware/issrc/blob/is-6_7_1/license.txt
- https://jrsoftware.org/inno-setup/purchase
- https://jrsoftware.org/files/is6-whatsnew.htm

## Native CI findings

Run 45548932515 failed because a single pipeline result became a string,
so indexing selected the character C rather than the path. Fixed at
89acdb4 by forcing array semantics. Run 45550141138 then reported
frontend file version 0.0.0; upstream ISCC.dpr uses ISDllGetVersion for
the loaded compiler engine, distinct from frontend file metadata. Record
frontend version only; require the exact actual compilation engine banner.
No compiler trust claim or fallback installation. Repeat native CI.

## 2026-11-25 upstream delta and migration gate

The official Inno Setup 6 revision history identifies 6.7.4 (2026-10-28)
as a newer stable 6.x release than the qualified 6.7.1. Scope review:
the COM Automation lifetime fix is not used by the current simple
Pascal launch predicate; the example PowerShell absolute-path fix
does not match any current installer script invocation; archive
extraction fixes do not match current explicit [Files] entries.
The 6.7.4 RedirectionGuard inheritance correction is potentially
relevant: the product uses admin installation and runasoriginaluser.
Current silent lifecycle evidence does not prove the interactive
non-elevated child mitigation behavior. Do not disable RedirectionGuard
as a workaround. Qualify the updated engine and interactive launch
before changing the production compiler pin.

Immutable upstream release is-6_7_4 published 2026-10-28T19:24:58Z.
Tag object bd24eaa852bc9f73f45aee2daa815e8baf89d745,
commit c2913c993858a781fcb455bac8b8949c1c366cb8.
Official executable asset 686086859 (10604576 bytes), SHA-256
a549929319f9120716677c685535ca4671e4b937b5fdc87e2585f32d8eb30e8c;
ISSig asset 686088463 (376 bytes), SHA-256
da04c2bd518c3c316f8783560ede99bd74973721c20d316f25370408673cc036.
Both downloaded bytes match REST digests; ISSig independently verified
with the reviewed def02 key. Vendor repository security-advisories
endpoint returned an empty list; this is not a comprehensive CVE check.
Local gh lacks release verify-asset support. Separate native Windows
job verifies the exact asset, Authenticode publisher/timestamp and
immutable release attestation without executing the asset. Pending.

No change to 6.7.1 compiler, historical evidence pins or release workflow.
Next: exact 6.7.4 component inventory and license delta, controlled
native compiler/installer qualification including notice upgrade,
interactive runasoriginaluser behavior and new candidate attribution.
Do not assume prior 6.7.1 binary evidence transfers.

References:
- https://jrsoftware.org/files/is6-whatsnew.htm
- https://github.com/jrsoftware/issrc/releases/tag/is-6_7_4
- https://jrsoftware.org/inno-setup/downloads/verify

## Native 6.7.4 publisher and exact component delta

PR #234 head b20d37a4843942f4e8dbf484a4a14f3a32a449b4,
run 45631933833, job 139267148940: PASS.
Artifact 15032445044 SHA-256
d4e07fe5e77f57f2e13fc2923912947f9d15ab98a4c7233c0c00afbcc51e0a44
matches REST. Authenticode Valid, publisher Pyrsys B.V., signer
certificate matches the reviewed 6.7.1 certificate; timestamp
certificate SHA-256 d14751ba71cd8883e560166406cf62cd229a5fe91e308d301976feb23ea90156.
Verified immutable release attestation names jrsoftware/issrc and
is-6_7_4, exact EXE/ISSig digests and GitHub release identity,
timestamp 2026-10-28T19:25:10Z. No AJAZZ signer trust asserted.

The previously reviewed innoextract 1.13.0 binary (SHA-256
c898db2ecc282ff8d943e9868d03dd6f1fc6069ddd40430341b211f93826b360)
was reused in a fresh unprivileged chroot to unpack the exact vendor
EXE, without running it. Comparison of the same 38 top-level
compiler inputs: 25 unchanged, 13 changed (seven executable/engine
files and six signature sidecars). All 17 extracted signed component
sidecars verify against the existing pinned vendor public keys.
Comparison evidence SHA-256
db75ea31a7b0e078f93aab951e92c5236af61d4e38ac925bd185290717cd9f78.
The new exact component pin manifest is
`config/inno-674-component-pins.json`, and the local verification
evidence SHA-256 is
3b1b3f84716b5095ad7f1395c1b025f9413d403ee1a6485b33c620207797e6a1.
This remains scoped input identity, not a loaded-component trace.

A separate hosted probe extends the previously successful trust
workflow. Only after asset hash, native Authenticode and release
attestation verification does it deploy the vendor compiler in
the upstream documented /PORTABLE=1 mode into a fresh runner-temp
directory. It requires all 38 exact inputs before and after
compilation and the exact 6.7.4 engine banner. An inert LICENSE-only
fixture exercises install/hash/uninstall with lowest privileges
and no application launch. Only JSON evidence retained.
Native compiler probe result pending. Production wrapper and
release workflows remain pinned to 6.7.1.

## Native 6.7.4 compiler fixture and product qualification

PR #236 head 6fb7aa8021b1725b8b04342726435930d5b7d64f,
hosted checkout b93e9f21cfd73824372a9f4ee7f0c8369614abcc,
run 45638049761, job 139288731383: PASS. Artifact 15034126967
SHA-256 ff5ca8dba9e4f69bf967511d17bd3a040d3b549766ed1648a10f3082f138550d
matches REST; exact three JSON members. Component evidence before
and after compilation byte-identical, all 38 inputs MATCH.
Inert fixture setup SHA-256
35fbcfdaadabff34563a72d91bc31efd84d1df0b2128df87f8c02b432b248a94;
payload MATCH, uninstall REMOVED, product_installed=false.

The next hosted qualification extends the isolated portable 6.7.4
job with the same pinned .NET 11 SDK, notice staging and product
clean/upgrade/repair/uninstall checks as the 6.7.1 notice workflow.
The explicit compiler directory and /F output override distinguish
the unpublished 6.7.4 probe. Inputs checked before and after actual
product compilation, exact engine banner required. The existing
upgrade script accepts only two explicitly enumerated probe filenames;
default behavior unchanged. A separate JSON binding ties component
observations to product setup, app, BOM and checkout identity.
Only JSON artifacts are uploaded, no release binaries or production
compiler changes. The new product probe result is pending, as are
interactive UAC observations and exact generated binary attribution.

## Scoped 6.7.4 product binary attribution

The reviewed 6.7.4 templates retain the narrow unsigned PE32 layout
used by the prior verifier. Exact new loader and engine SHA-256 pins
are respectively:
998c58046b0808e75a030859962e1fe1ea600e8a5cf4646b09aadce77342c1a9
and
0c94d43e2c0f4d8371a2e1813b5446f3bc85ece3211dc4a6676159b534bbc483.
Source comparison shows the Shared.Struct version constants changed,
but no offset-table format change in the reviewed delta.

The 6.7.4 product workflow now retains a local copy of the actual
installed uninstaller immediately before executing it, checks the
copy hash against the executable, and emits a removal record only
after successful cleanup. The scoped verifier binds that record to
the exact product setup/source/application identity, checks pinned
loader and engine non-resource bytes, validates the offset-table and
compressed engine CRCs, then attributes the uninstaller PE and
AppId/message frame to the recovered engine. Existing 6.7.1 pins and
verifiers are unchanged. Only JSON evidence is uploaded.
Two regressions pass; actual hosted attribution pending.
Resource content, message semantics, compiled script, solid payload
attribution, interactive acceptance and release admission remain open.

## Native 6.7.4 product lifecycle and scoped SBOM result

PR #238 head 63a0f973a2f28d8b7fec19cc068a857ff4c02465,
hosted checkout bfa6ffcc5225255c008004839fe7fe9718b1ed9a,
run 45638993065, job 139292075013: PASS. Exact archive digests
matched REST for these three evidence artifacts:

- Clean 15035156390:
  29be74e532690fca4c240b3ff0649bd34302d79503cf4b1fc7941b4b7e937417
- Upgrade 15035006804:
  e9e3d9e11caf5fd8b0068f41d6362c3d81db33807cf0b89da295d518223c226a
- SBOM 15033382633:
  b6fe18d056e4ac303bfab61dc0006730ca00113b47283027c592128eb805b92f

Clean and upgrade lifecycle bytes match the bound hashes; all three
notice records equal, all 38 compiler inputs match before/after.
Setup SHA-256 2efcfd3901351a3ba40e9a285cf952a25190b4cc92a1cae1e27674a28361d99e;
app SHA-256 fd78cc38ec0b26d75a2fc3bf06208027fd5667068eef7db04fb4301ec1553733.
Repair PASS, synthetic data PRESERVED, uninstall REMOVED, tray launch
NOT_OBSERVED. Native interactive acceptance remains NOT_VERIFIED.

269-component scoped SBOM SHA-256
3701b1ec71532830b25b2734633aca6823d9db9fa9bd92fb9ea470feb104026f
passed independent CycloneDX schema and candidate binding; evidence
SHA-256 51789a00b7bdc792f38143bd87adeafc42ebb30d1600b6e29bc334e763a264f6.
Replayed the retained Nov25 NuGet snapshot and OSV response against this
exact new BOM (no new acquisition): four package identities match;
no matching ranges/IDs. Evidence SHA-256 respectively
8c5a7b8d9acf7cd10eb5951a3bd8f4f3660042d56677a6c5e37b3d960b8eb60a
and b86670a1d2108dfd64e9c32f5b4efe335916947d9d139614f244d350b8fce34e.
No freshness gate, full vulnerability clearance or legal admission.

## 6.7.4 resource and English message qualification

The actual extracted official loader and engine have respectively 45
and 81 resource leaves, every key and payload digest identical to the
reviewed 6.7.1 templates. The observed template comparison is scoped
to leaf payloads, not a claim of equal PE code or directory serialization.
Default.isl and Shared.SetupMessageIDs.pas at the pinned 6.7.4 source
match the prior exact pins; reconstruct the 281 English message
strings in enum order (25120 bytes), SHA-256
31b34a6d0f6d21f25e92c7ef6fcb03067654b5dd16df3416374f2d12ed4b3dbd;
reviewed language options SHA-256
20818b0695dca2c6bd625d633b29e98f012f3db4e0d16c2c05f447bacb563e0a.
The current project icon also matches its existing pin.

A separate 6.7.4 verifier checks the actual prior binary evidence,
pinned template/icon identities, recovered engine, exact leaf changes,
version and manifest transforms, observed resource serialization
and English message bytes. Two regressions pass. The actual product
resource and message result awaits hosted CI, and solid payload,
compiled script, interactive acceptance and release admission are
not verified. Production pin remains 6.7.1.

## Native 6.7.4 binary and resource attribution

#239 exact head 7f5b9cb56349dde7ab2e26bc655ca1b7a8f00db2,
run 45639593361, job 139294214890, passed 6/6. Binary evidence
artifact 15035475586 ZIP SHA-256
6bf84d2e73808275d1b88947d41951d31b0987a9ef1da2c24b518fc65b352737;
binding artifact 15035425989 ZIP SHA-256
c98767eb322576bbad1149820a81721b56125c8d31a7a64f1d1a6819f72ca9fb.
Both matched REST; source/setup/app and exercised uninstaller hashes
match across records. Loader/engine non-resource sections MATCH;
325 engine chunks CRC-checked, 4496384 decoded bytes. Engine SHA-256
6a8e8465e229cf2e7d70e698ff4ef9c82a238c31aa0416f79c8cae486793eb53.
Actual uninstaller PE matches recovered engine except reviewed mode;
message structure matches. Binary JSON SHA-256
c8efc297c32a9a825fc2424c12158051dddb8e741d9e132e15bfe056d64ac4fd.

#240 exact head 90a8e189ba8bde7b3f8bb7b67021637c7ad650ae,
run 45640223414, job 139296497263, passed 6/6. Resource artifact
15035352163 ZIP SHA-256
0175f458a579855ed2843ceea4266dae7d90ce099adb3b2979b66a2cad4ddd93;
binary artifact 15035302431 ZIP SHA-256
632a3a7d0d45df1dc43c186c1efe95f377ec500c76dc2f033c18638ada125dcf.
Both matched REST; resource JSON references exact binary JSON hash.
Resource evidence SHA-256
1d87cbee8aa5bc2ffcf851c8602c752c952041d02675e99e7801f00c47422e2f.
Setup SHA-256 ae47ad41b6869168b479bb5058b2f4e53cb4ab9ae983c3ea789afb0cf8c2ed8c.
Loader 25 leaves, 32 directories; engine 71 leaves, 80 directories.
All scoped icon, version, manifest, resource serialization and padding
checks PASS; 281 English messages and language options match.
No unqualified resource leaves in this scoped observation.
The distinct candidate setup identities must not be interchanged.

The next probe validates the exact ordered 15 source files (application,
four icons, nine notices and manifest). The reviewed compiler merges
duplicate source filenames, not identical contents at distinct paths.
The verifier requires 16 file records including generated uninstaller,
15 locations, exact extent/flags/hash, bounded LZMA2 decompression,
terminal state and per-file hash; checks scoped IFPS launch predicate.
File destination records and remaining Setup.0 records are not yet
qualified by this tool. Actual native result pending. No release change.

## Native 6.7.4 solid payload and IFPS result

PR #241 head 177001c8d667dbc4b7445dd193e88bc3ae469253,
hosted checkout 111439eb40f8038690f24e8a1b4e553ae76028eb,
run 45641200908, job 139300000991: PASS (7/7 CI).
Three exact archive digests match REST:
- Solid 15036335309:
  e79d782d0a77a74170d60a61beb315486b41d2560175a19ef1b3d0efb03a1a3a
- Resources 15035970459:
  0ef1f4fe937d7f19429605b6f3483e05c90ed00a31943a06ed57c96751552328
- Binding 15036040398:
  1610d6ca5522e8c4f53e280eb8a52863b273a25a6592494790889b09d2c6a997

Solid evidence SHA-256
10111f99b8030a7020b98ccfa61bde0c8847c39e564f6f7d59ba96d75a861c46.
Setup SHA-256 e26cb9b41685ba42a78100111d0fd803de1c596513ba6f9de31b3335ec2635b7;
app SHA-256 71950f5df7b29a9c91ec7d114623db580000d54e6b718f778871a6f33a3e81b0.
All fifteen decoded source file hashes match. Setup.0 decoded block
sizes 48397 and 1335 bytes (15 location records), CRC and terminal
state PASS. IFPS 32 types, four procedures, two globals, 27 instructions,
only EXPANDCONSTANT and WIZARDSILENT imports. Exact bytecode SHA-256
ec37558245fc7a7712e9e023f36cce2ce5150d268f19c7c7fbe7a69cb8d27ebf
matches historical reviewed launch policy. Static semantic scope only;
no independent recompilation or IFPS runtime execution by the verifier.
#241 merged into draft integration #99 at 3c9dbb0.

## Complete scoped Setup.0 record qualification

The new verifier binds the exact solid evidence, source LF-normalized
SHA-256 d2876f4209f244033dd92dd19a6f9e9d641ca3cbed441b4dbd020923492f9ef8,
pinned language inputs, and exact 6.7.4 ISCmplr.dll SHA-256
236555054ca65194c69544b4ef1d49ea345259745f5c4a2005aca7b5674e7cff.
Both official wizard RCDATA hashes match the previous reviewed images.
It checks the header, language and custom messages, task, 16 ordered
file records including the generated uninstaller, two shortcuts,
one launch record, both images, and exact end of the decoded block.
Two synthetic regressions PASS. Native verification pending.
No release compiler change, interactive acceptance or legal clearance.

## Native Setup.0 result and single-run migration evidence

PR #242 head af8eeb8e005890a3822570991f03d9423dcff5e4,
hosted checkout aac75c9b5d419d7e12756bc59fb56e4cad2a35db,
run 45642394292, job 139304257773, 6/6 checks PASS.
Merged into draft #99 at dfa8202 after exact tested tree comparison.
Setup SHA-256 d59e5797b5c7c2bb86d83f4b416ff028892e6dad74a0b63dc6c11140a99ec911.
App SHA-256 dca7a7b287d8ffa7cdc7929a03337497d8041e5c4315d56a94b47ac34d1a9c26.
Setup.0: all 48397 decoded header bytes accounted for, 16 file records,
two shortcuts, one run entry, 281 standard and 12 custom messages,
both pinned wizard images, zero trailing bytes. Evidence SHA-256
503632572297a34d67a6f5377ab53327900e5317165c66e0a23b0bfcc5b3076a.

The seven same-run archives were downloaded and checked against
REST SHA-256 digests (artifact IDs 15036381320, 15036146531,
15036156393, 15035757566, 15036361306, 15036835658, 15036116452).
Twelve exact JSON documents were joined using the new
verify_inno674_migration_evidence.py, verifying eleven raw digest
edges, shared setup/app/source identities, lifecycle outcomes,
compiler evidence, scoped SBOM binding, binary/resource/solid and
Setup.0 attribution. Actual replay PASS; joined evidence SHA-256
fce873d5d3ac5953e01aa0a20448f768da472dc79cc3eb932b8a2ad8206030c0.
This is a scoped consistency check of reviewed native evidence,
not independent authentication or complete distribution clearance.
New CI emits only the joined JSON. Mixed/missing evidence regression
tests pass. Native rerun pending. Production compiler remains 6.7.1;
migration, signing, advisory freshness, independent schema check of
the new exact BOM, distribution terms and interactive/hardware
acceptance remain separate gates. Release hold unchanged.

## Exact #242 SBOM and migration checkpoint

The independently validated #242 BOM SHA-256
3416f7d8f9c205422f73efc7597c8804b0be8c90b84461ec7400db2023881475
matches the joined product evidence. Independent CycloneDX Draft7
validation and candidate binding PASS; evidence SHA-256
b238afa21a260efa1e4bcbda865330897811f9a4d58b91cc44f7091cf519f019.
The retained Nov25 NuGet and OSV observations were replayed on the
exact BOM, not freshly acquired; four exact source packs, no matches
or IDs. Evidence SHA-256 respectively
0be0bbf6cbbeb7811cb6145582d251171ada84032be5597b517fd9c22fbd68a5
and 96728ee180c20662abe1383b747e48bb8e63ef3bba71702a5ab53a1ff6864641.
No freshness, installer-wide, OS or full transitive advisory clearance.

Migration checklist:
1. Verify exact #243 hosted joined evidence and integration tree.
2. Prepare a distinct non-publishing production-shaped build using
   exact 6.7.4 portable inputs, normal output filename/version policy
   and reviewed notice inclusion; repeat same-run binary qualification
   and normal upgrade tests. Do not substitute notice-probe evidence
   for a different production-shaped binary.
3. Review complete distribution notices, signer trust and terms.
4. Record actual RG01-RG06 interactive UAC observations and required
   device/OS acceptance. A silent hosted test cannot establish these.
5. Only after review of the exact resulting candidate may production
   compiler/notice selection and release admission be considered.
   Preserve the 6.7.1 historical baseline and manual release hold.

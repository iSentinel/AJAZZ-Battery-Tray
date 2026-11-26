# Inno Setup 6.7.4 product launch qualification

Scope: proposed unpublished migration from 6.7.1 to 6.7.4.
Do not treat silent installer, fixture or compiler success as proof
of the original-user launch behavior. Keep the production pin and
release hold until the new product candidate is qualified.

## Exact upstream source comparison

Compare reviewed commits cfdf48923178df4b4f040e038b423aa555a61ffc
and c2913c993858a781fcb455bac8b8949c1c366cb8. The GitHub comparison
reported 31 commits and 71 changed files. In Setup.MainFunc.pas,
InitializeSetup no longer calls RedirectionGuardConfigure before
respawning Setup for elevation. The revised ISHelp/isetup.xml and
6.7.4 revision history clarify the child-process inheritance boundary.

The AJAZZ installer specifies PrivilegesRequired=admin and
runasoriginaluser; its launch predicate disables silent launch
by default, explicitly enables /LAUNCH=1 and disables /LAUNCH=0.
The new upstream behavior is relevant when Setup actually requests
elevation and starts the application using original user credentials.
A pre-elevated or lowest-privilege process can still inherit the
mitigation. Do not disable RedirectionGuard to force a passing test.

## Acceptance matrix

| ID | Starting context | Launch control | Required observation |
|---|---|---|---|
| RG01 | Standard interactive desktop, UAC elevation actually occurs | Default interactive | Single tray in original user session, non-elevated token, no inherited mitigation on supported OS |
| RG02 | Same interactive context | /LAUNCH=0 | No tray launched |
| RG03 | Same interactive context | /LAUNCH=1 | Single tray, original user credentials; mitigation observation as RG01 |
| RG04 | Already elevated interactive Setup | Default interactive | Observe actual child token and mitigation; inheritance is documented, not automatically a regression |
| RG05 | Elevated CI runner, silent Setup | Default silent or /LAUNCH=0 | No tray launched; no conclusion on RG01 |
| RG06 | Supported standard desktop with a separate explicit test account | Install, upgrade, repair, uninstall | Expected file integrity and cleanup; synthetic user settings/history preserved |

Before RG01-RG04 record the exact OS build, setup hash, app hash,
engine version, initiating token/session and actual UAC transition.
Use read-only process token/mitigation observation; never manipulate
junctions, disable protections, collect credentials or change local
security policy. Record observations of supported mitigation API;
if the API or desktop is unavailable, use NOT_VERIFIED rather than
assuming the mitigation is disabled. The installed application
launched independently from Setup is a separate observation.
No real hardware or real-user migration is inferred from these cases.

## Candidate requirements

- New compiler input manifest and before/after identity must match.
- Separate 6.7.4 product-probe filename and hash-bound lifecycle
  evidence; existing 6.7.1 workflows are retained until migration.
- Clean installation, beta.60 upgrade, missing-notice restoration,
  uninstall and synthetic-data preservation must pass.
- Requalify exact loader, engine, generated uninstaller, notices,
  SBOM, advisories and signing; historical 6.7.1 evidence does not
  transfer to new executable bytes.
- Record real interactive acceptance independently of hosted silent CI.

Source: https://github.com/jrsoftware/issrc/compare/cfdf48923178df4b4f040e038b423aa555a61ffc...c2913c993858a781fcb455bac8b8949c1c366cb8

## Local checklist validation

Use the exact joined native qualification JSON, not an unrelated
portable build or a historical installer. Generate a local checklist:

```sh
python3 tools/verify_interactive_acceptance.py --candidate migration-evidence.json --output interactive-checklist.json
```

The generated RG01–RG06 rows are all NOT_RUN. Only after verifying
the actual setup and app SHA-256, record the actual numeric OS build,
status and brief redacted observation per tested case. Follow the
matrix above, not the presence of the form. RG05 hosted silent testing
does not substitute for RG01–RG04 or RG06. Keep the notes private;
do not include user names, device paths, serials or credentials.
Use a private local directory; the tool does not upload any input.

```sh
python3 tools/verify_interactive_acceptance.py --candidate migration-evidence.json --checklist interactive-checklist.json --output interactive-review.json
```

Exit 0 means the record structure and candidate identity are valid,
not that cases passed. The summary omits observation text and always
retains independent acceptance and release admission as unverified.
The exact #246 setup is not available for download from its JSON-only
qualification run. Do not substitute another binary or invent results.

### Optional local binary binding

Supply both exact executables to check their actual local bytes against
the native qualification before creating or reviewing a checklist:

```sh
python3 tools/verify_interactive_acceptance.py --candidate migration-evidence.json --setup AJAZZBatteryTray-Setup-win-x64.exe --app AJAZZBatteryTray.exe --output interactive-checklist.json
python3 tools/verify_interactive_acceptance.py --candidate migration-evidence.json --setup AJAZZBatteryTray-Setup-win-x64.exe --app AJAZZBatteryTray.exe --checklist interactive-checklist.json --output interactive-review.json
```

Both options must be supplied together. The existing bounded regular
file reader rejects missing, oversized or symbolic-link inputs, and
the hashes must match the exact candidate evidence. The review reports
local_binary_binding MATCH or NOT_PROVIDED. A template generated after
checking binaries has the same checklist schema as an older template;
the check is repeated at review time. No binary is executed, no
Authenticode trust or test execution is inferred, and no release is
authorized. JSON-only hosted evidence does not supply the setup bytes.

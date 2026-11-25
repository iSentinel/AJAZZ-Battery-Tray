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

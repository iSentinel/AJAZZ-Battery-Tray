# Windows Setup lifecycle

The normal interactive installer closes applications using the installed
AJAZZBatteryTray.exe through Windows Restart Manager, with graceful closure
only. A confirmation page can appear if the image is in use. If shutdown
cannot complete, do not ignore the file-in-use warning or force kill: close
the tray manually, wait for diagnostics to finish, and retry. A portable
copy in another directory or another interactive session is not covered.
An existing beta.60 instance does not have the new explicit shutdown
window, so its transition needs separate field verification.

After successful installation Setup launches the installed image once,
before the final wizard page, with original-user credentials. Windows
cannot recover the original non-elevated token if Setup was started with
Run as administrator or from an elevated shell. Start Setup normally
and allow its own UAC request. Silent installs preserve no-launch by
default; /LAUNCH=1 explicitly opts in, /LAUNCH=0 opts out.

## Commands (candidate only)

```powershell
# Normal interactive installation/update from a standard user shell
.\AJAZZBatteryTray-Setup-win-x64.exe

# Silent update without auto-launch (not a dry-run)
.\AJAZZBatteryTray-Setup-win-x64.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /RESTARTEXITCODE=3010 /SP- /CLOSEAPPLICATIONS /NOFORCECLOSEAPPLICATIONS /LAUNCH=0

# Silent update and launch, in an interactive user session
.\AJAZZBatteryTray-Setup-win-x64.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /RESTARTEXITCODE=3010 /SP- /CLOSEAPPLICATIONS /NOFORCECLOSEAPPLICATIONS /LAUNCH=1
```

There is no supported installer dry-run yet (ENG-07); /VERYSILENT
modifies the target. A successful installer exit is not proof of tray
readiness. The new CI test observes two synthetic processes using the
installed image and checks graceful exit, exact upgraded binary hash,
registered version, new PID and readiness. The CI-only installer
compile switch is not used for release builds. The test performs no
HID, history or notification activity. Physical running beta.60 upgrade,
in-flight diagnostic and standard-user UAC acceptance remain open.

No release dispatch, new HID commands, forced close, or changes to
settings/history deletion policy. Published beta.60 remains unchanged.

References: [CloseApplications](https://jrsoftware.org/ishelp/topic_setup_closeapplications.htm),
[Run](https://jrsoftware.org/ishelp/topic_runsection.htm).

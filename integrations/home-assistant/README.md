# Optional local API preview

This separate .NET 8 console project is an experimental read-only consumer,
not a complete Home Assistant integration. It is not included in the tray
installer or portable distribution, has no automatic startup or service,
and has no MQTT dependency.

## Manual use

1. Run the tray version beta.52 or newer and explicitly start Local battery API.
2. Keep that window open. Use Copy API token; never put the token in a command
   line, environment variable, saved configuration or issue report.
3. In a local interactive terminal with the .NET 8 SDK installed:

```powershell
dotnet run --project integrations/home-assistant/AjazzHaPreview.csproj -c Release -- --help
dotnet run --project integrations/home-assistant/AjazzHaPreview.csproj -c Release
```

4. Paste the token at the hidden prompt and press Enter. Choose a displayed
   session row number and confirm with y. The program reads one more snapshot,
   validates that the API session still matches, prints fresh battery percent
   or an unavailable status, and exits. Use q at the row selection to exit.
   The token and mapping are not saved. Clear the clipboard after pasting.
5. Stop Local API from the tray when no longer needed.

The optional --port argument accepts ports 1–65535 (default 18789);
the destination is always 127.0.0.1. Redirected input is rejected. Exit
status 0 means fresh preview or user cancellation at selection, 1 means
unavailable/request failure, and 2 means invalid arguments or selection.
No device name is inferred from a slot. Restarting the API invalidates
previous bindings. No external network or hardware commands are used.

## Development stage

The executable is built separately; its own CI checks help, invalid port,
redirected input and the absence of a tray project reference. The shared
consumer's loopback test covers actual authorized reads and API restart.
Interactive entry and real-device selection still require Windows acceptance.
A future optional bridge will need an explicit stable user mapping, protected
credentials, authenticated TLS transport and availability/expiry behavior;
this preview does not publish anything to Home Assistant.

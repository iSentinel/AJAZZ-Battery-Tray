# Application branding

The orange-shell wireless mouse with green battery badge is static application
branding, not live telemetry. Windows embeds the multi-resolution ICO in its EXE
and Inno Setup package. Both Apple bundles use the shared ICNS resource declared
in Info.plist. Existing dynamic battery/status tray icons are unchanged.

The checked-in JPEG is a verified reduced 144x144 derivative of the generated
artwork. Larger platform resource sizes are interpolated; this is a development
candidate, not a claim of native high-resolution art. The original generated
image is retained in the conversation. The icon is not a device identification
or a claim of manufacturer endorsement.

CI must compile and package each edition; verify the physical appearance in
Explorer, the installed shortcut and Finder separately. No new HID commands,
settings, runtime dependencies or release publication.

## Color themes

AJAZZ lists White, Black, Blue and Orange for the AJ179 APEX series:
https://ajazzstore.com/collections/wireless-mice/products/ajazz-aj179-series?variant=43846682443829

The bundled art variants are derived from the reduced generated orange icon
by deterministic warm-hue recoloring, not exact manufacturer color samples.
Windows Settings offers independent Application icon and Default tray color.
Application icon selection affects the running Device Manager and neutral
tray icon, not the immutable EXE/installed shortcut resource (orange).
Per-device USB/AULA color overrides inherit the global selection by default;
BLE uses the global choice. Normal AJAZZ tray can show a mouse silhouette
or the percentage. Fresh 11–20% remains amber numeric, <=10% red numeric.
Unknown/cached is gray, cached retains asterisk. AULA remains numeric.
Native Windows hover text includes percentage and chosen color name, not
rich colored text. Settings are persisted locally, not portable backup v1.
Both Apple editions expose independent app and tray color menus and mouse/numeric style.
Their runtime application image changes through AppKit; the signed bundle/Finder
icon remains the build-time orange resource. Native CI and owner UI checks are separate. No HID or alert threshold changes.

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

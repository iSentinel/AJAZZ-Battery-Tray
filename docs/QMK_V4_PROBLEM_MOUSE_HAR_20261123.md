# qmk.top/v4 problem-mouse HAR — evidence review (2026-11-23)

## Scope and provenance

Owner supplied one Chrome DevTools HAR named
`qmk.top_*.har`.
**The raw HAR is not committed** because request headers and future
captures may contain sensitive information. This note records only
aggregate metadata extracted from this single supplied file.

## Observed in this HAR

| Property | Observed |
| --- | --- |
| Time window (UTC) | 2026-11-23 14:12:02.245 to 14:12:38.115 |
| Total network entries | 9 |
| HTTP methods | 9 GET; no POST |
| HTTP responses | Six 200, three 304; no HTTP error statuses |
| Origin | qmk.top only |
| Resource categories | 5 scripts, 2 stylesheets, 2 image requests |
| Browser User-Agent | Chrome 157 on Windows NT 10.0 x64 |
| Request bodies | None |
| WebSocket messages | None |
| Device-specific API calls | None captured |
| USB/HID report exchange | Not represented by HAR |

The asset `mouse_rongyuan_new.b2a583d5.png` was requested twice.
Its filename does not identify the actual attached mouse model.
One bundled JavaScript response included UI code mentioning HID
key names; that is **source code downloaded by the browser**, not
a trace of executed WebHID calls or reports.

## Conclusions and limitations

- The HAR is consistent with normal frontend asset loading. It does not
  demonstrate successful or failed battery telemetry for any mouse.
- The reported browser User-Agent identifies **Windows**, not the
  owner's separate iMac/macOS High Sierra 10.13.6 system. The capture
  cannot validate High Sierra compatibility.
- No VID/PID, HID usage, battery percentage, IOReturn, or WebHID
  feature report bytes are present in the nine network entries.
- Do not conclude that the receiver works, is broken, or needs a
  protocol change based on this HAR.

## Next required evidence

1. For the iMac, use the experimental High Sierra .4 app's
   `--trace-hid` CLI to obtain IOKit open status, approved F7
   SetFeature result and 05 GetFeature result/length. Review
   response prefix before sharing; no alternate or vendor
   configuration command should be sent.
2. For the problem mouse in Chrome, capture a *console* diagnostic
   of WebHID permission, selection, read errors and model/receiver
   metadata where available. The Network HAR alone is insufficient.
3. If comparing a working and affected receiver, obtain separate,
   clearly labelled traces captured with the same connection method,
   browser and test sequence. Redact identifiers/tokens before
   publication or issue submission.

## Release gate

Neither a new parser fallback nor modified live HID requests should
be introduced until a real HID response or failure code has been
recorded and linked to an identifiable receiver/OS combination.

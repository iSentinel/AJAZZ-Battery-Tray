# Routine HID polling worker cost baseline

The draft audit's isolated full-HID capture has a synthetic sample
worker that starts the published .NET process and transfers a small
known JSON result over stdout, with no HID calls. Before applying
process isolation to routine polling, measure this lower bound.

Use a Windows executable built from draft PR 99 or a descendant:

    powershell -NoProfile -File tools/Measure-PollWorker.ps1 -ExePath .\AJAZZBatteryTray.exe -DryRun
    powershell -NoProfile -File tools/Measure-PollWorker.ps1 -ExePath .\AJAZZBatteryTray.exe -OutputPath .\worker-baseline.csv -Iterations 20

The benchmark starts one worker at a time and verifies its exact
synthetic output. Each worker is bounded by a timeout. CSV rows are
written after successful iterations, and an existing file is never
overwritten. It reports wall-clock p50, p95 and maximum using
nearest-rank quantiles, and the p95 share of the shortest supported
15-second polling interval. The GitHub Windows build runs 20 samples
and publishes the CSV as a separate CI artifact.

This measures process startup, runtime initialization, stdout and
exit on that machine. It does not measure native HID enumeration,
radio latency, CPU usage, real poll energy or memory, or cold-start
behavior under every host condition. CI timing is not a hardware
acceptance result.

Next: record the same benchmark on the owner's Windows PC and
measure steady-state application resources using Measure-TrayResources.ps1.
Compare a supervised process with a persistent worker before changing
default polling. Repeat on macOS separately. No runtime polling
strategy has been changed by this tool.

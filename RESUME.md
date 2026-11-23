# Resume — USB discovery allocation candidate

- beta.53 release 45139628072 PASS, six assets verified.
- PR #70 offline optional HA MQTT availability merged
  10be9fde200ffd0b7f775ff62763a768c10c7a63.
- PR #71 MQTT acknowledgment/order, non-retained battery state merged
  096778a40bc807d83643273a5a0527baea1d2001.
- PR #72 optional broker TLS parameter preflight pending CI; no network.
- perf/reconcile-scratch-reuse reduces repeated known USB inventory
  allocations by lazy scratch reuse, preserving polling deadlines and
  no changes to HID reader. Ten additional pure C# checks pending CI.
  Python 23/23 PASS. No benchmark improvement claimed.
- Next: verify PR #72 and this branch CI, prepare beta.54 metadata
  only after successful initial checks. Real Windows measurements,
  AULA sleep/recovery, AJ159 affected capture and multi-BLE pending.

# Resume — beta.53 AULA API continuity release candidate

- beta.52 published; release workflow 45093197963 PASS; six assets.
- PR #68 merged a1f280379e68504a1d39fc55daf5f3ff3f51e534;
  standalone HA preview EXE SHA256 verification PASS.
- PR #69 exact head 4c34a1151c7e18c40185c3d9db571da4d19ce2a4;
  Windows 45096569893, macOS 45096569901, preview 45096569934 PASS.
- Beta.53 version, installer, macOS build, release workflow and changelog
  metadata prepared; MUST verify final HEAD CI before merging and publishing.
- AULA API slot 1 unbindable status; known receiver gets non-reused ordinal,
  replaced/unknown identities retire previous slots; same receiver during
  no-reply sleep retains slot. Ten continuity assertions, not physical proof.
- No MQTT/broker/HA runtime included. Optional CLI remains separately
  run only on explicit user action.
- Next after beta.53 publication: offline MQTT availability/expiry policy,
  no network access/broker credentials until opted-in transport gates.
- Actual Windows resources, AULA long sleep, paired AJ159 reports/HAR,
  two-device BLE and interactive preview remain open.

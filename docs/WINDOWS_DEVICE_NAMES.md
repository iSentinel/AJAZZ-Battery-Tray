# Windows Device Manager friendly names

## Scope

The owner's goal is recognizable names in the standard Windows Device
Manager, not just in AJAZZ Battery Tray. Windows exposes the per-instance
DEVPKEY_Device_FriendlyName property; DEVPKEY_NAME reflects the friendly
name when present, otherwise the device description.

References:
- https://learn.microsoft.com/en-us/windows-hardware/drivers/install/devpkey-device-friendlyname
- https://learn.microsoft.com/en-us/windows-hardware/drivers/install/devpkey-name--device-instance-
- https://learn.microsoft.com/en-us/windows/win32/api/cfgmgr32/nf-cfgmgr32-cm_set_devnode_propertyw
- https://learn.microsoft.com/en-us/windows-hardware/drivers/install/devpkey-device-parent
- https://learn.microsoft.com/en-us/windows-hardware/drivers/install/enumerating-installed-devices

## Stage A — beta.32 read-only preview

Use Settings > Windows device names preview. No administrative privileges
are requested. Only present exact USB root families 3151:5007 and 05AC:024F
and candidate HID MI_00 children are considered. Verify parent ancestry
through Configuration Manager, and read root hardware IDs to obtain USB
revision. The suggested labels are based on owner-observed receiver
revisions, not universal model identifiers. An unknown revision remains
generic. AULA IDs are shared with other models.

The preview lists a temporary group number, family/revision, role, current
display name (FriendlyName or DeviceDesc fallback), and proposed name. It
does not display instance IDs or export this inventory. It does not write
Windows properties or send HID traffic. A failure or missing candidate
must not be interpreted as proof of incorrect hardware.

## Stage B — guarded per-instance naming (not implemented yet)

Keep the tray unelevated. User confirms each physical receiver/model and
target node from a current inventory, then explicitly invokes a narrowly
scoped elevated operation. Revalidate presence, exact instance identity,
hardware family, model selection, parent relationship and the role/class
of each child immediately before writing. Refuse ambiguity, changed target
or missing metadata. Never apply to all devices sharing VID/PID.

Use only DEVPKEY_Device_FriendlyName with documented Windows API; not
DeviceDesc, hardware IDs, class-wide values, driver package edits, registry
permission changes, firmware, or device restarts. No automatic reapplication.

Before a write, save original property presence and value and exact local
instance identity in a protected, local rollback record. Distinguish absent
property from empty property and read failure. Read back the property after
each write. Restore only the same verified instance and detect intervening
changes; delete the property if originally absent. Handle partial failure
and report per-node outcomes. Never embed private instance IDs in logs or
diagnostic exports. The elevated component must validate all inputs and
must not expose a generic property-writing command.

## Physical acceptance

1. Connect only AJ159, open preview and check the receiver and mouse node
   share one group. Repeat for AJ179, then connect both.
2. Connect L99 and verify its own receiver/keyboard group independently.
3. Confirm model names manually; unknown or identical revisions must remain
   distinguishable without guessed identity.
4. When Stage B exists, test one confirmed node at a time, refresh the
   standard Windows Device Manager, verify name, normal device function
   and rollback to original property state.
5. Repeat after disconnect/reconnect. Windows may reset names when a new
   device instance is created or a driver is reinstalled, so do not promise
   persistent names across these events.

CI and physical validation are separate. Stage A does not change names.

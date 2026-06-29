# Roadmap

The current baseline is an installable Home Assistant custom integration with a
neutral `compact_9000_btu_ir` domain, service actions, and an optimistic
Climate entity. The next work should make it easier to use every day and easier
for other owners to help confirm compatible units.

## Climate And Voice Assistant Friendliness

- Improve the Climate entity for Home Assistant dashboards, HomeKit, Alexa, and
  Google Home.
- Keep exposed controls simple: HVAC mode, target temperature, fan, swing, and
  explicit on/off behavior.
- Avoid hidden automatic sends. A command should be sent because the user,
  automation, or assistant requested it.
- Keep mode constraints visible and predictable:
  - `dry` fixed to fan low unless new captures prove otherwise
  - `auto` and `fan_only` fixed to fan high unless new captures prove otherwise
  - `cool` allows low, medium, and high

## Convenience Features

- Keep `send_max_cool` as the confirmed remote-sendable maximum cooling state:
  Cool, 17 C, Fan High, Power On.
- Investigate whether panel Super-Kuehlung is actually different from Max Cool.
  This needs real-device observation, ideally with a power meter.
- Investigate Sleep mode separately. The manual documents it as a panel function
  and the current integration should not pretend it is a normal IR preset until
  behavior is captured or measured.

## IR Receiver State Sync

- Subscribe to Home Assistant infrared receiver signals.
- Decode matching Compact 9000 BTU frames.
- Update the optimistic Climate entity when the original remote is used.
- Ignore unrelated IR traffic safely.
- Document receiver setup and known limitations once implemented.

## Community Compatibility

- Collect confirmed captures for PEARL / Carlo Milano, electriQ Compact 9000
  BTU / COMPACT-V2, and other compact 9000 BTU white-label units.
- Keep Trotec / `TROTEC_3550` visible as a protocol search term, not as a
  hardware-origin claim.
- Expand `docs/compatibility.md` only when evidence is strong enough.


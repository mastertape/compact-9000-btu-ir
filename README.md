# Carlo Milano Compact 9000 BTU IR for Home Assistant

![Carlo Milano Compact 9000 BTU IR](docs/hero.png)

Home Assistant custom integration that adds a `carlo_milano_ir` service domain
and an assumed-state climate entity for Carlo Milano / PEARL Compact 9000 BTU
portable air conditioners controlled through Home Assistant's `infrared` entity
platform.

Tested device: Carlo Milano NX-7532-675 with REV1_2016 remote. Related-platform
research covers Carlo Milano NX-7532, possible NX-7532-919 variants, electriQ
Compact 9000 BTU / COMPACT-V2 candidates, and the `TROTEC_3550` protocol name
used by IRremoteESP8266.

[![Open your Home Assistant instance and open this repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=mastertape&repository=carlo-milano-ir&category=integration)

## Design Goal

This integration keeps the air-conditioner protocol knowledge in Home Assistant:

1. A compatible IR blaster exposes a Home Assistant `infrared.*` transmitter.
2. `carlo_milano_ir` builds Carlo Milano NX-7532 IR frames.
3. Home Assistant sends those frames through the configured infrared entity.

It does not add Carlo-Milano-specific buttons to ESPHome YAML and does not
require a dedicated ESPHome action for each air-conditioner command.

The protocol implementation is based on reverse-engineered Carlo Milano
NX-7532-675 / REV1_2016 captures. IRremoteESP8266's `TROTEC_3550` implementation
is used only as a compatibility cross-check for timing and bit-field hypotheses.
This does not imply that Trotec is the manufacturer or origin of the Carlo
Milano unit.

## Requirements

- Home Assistant with the `infrared` platform.
- Any compatible `infrared.*` transmitter entity.
- Tested reference emitter:
  `infrared.xiao_smart_ir_mate_ir_proxy_transmitter`.

No ESPHome YAML changes, flashing, or device-specific ESPHome services are
required by this integration.

## Compatibility And Confirmation Wanted

Confirmed with local captures:

- PEARL / Carlo Milano NX-7532-675
- REV1_2016 remote
- v0.1 climate control through Home Assistant and HomeKit

Likely related search targets that need community confirmation:

- Carlo Milano NX-7532
- Carlo Milano NX-7532-919
- electriQ Compact 9000 BTU
- electriQ COMPACT-V2
- Compact 9000 BTU white-label portable AC units with matching remote layout
- IRremoteESP8266 `TROTEC_3550` compatible protocol devices

Please open an issue if you can confirm another brand/model with photos,
manual links, type-plate data, or checksum-valid IR frames. See
[compatibility research](docs/compatibility.md) for the evidence that is most
useful.

## What v0.1 Provides

- A rudimentary assumed-state Climate entity for Home Assistant dashboards,
  automations, and HomeKit bridging.
- A bundled picon/entity picture for the climate entity.
- `carlo_milano_ir.send_hex`
- `carlo_milano_ir.send_state`
- `carlo_milano_ir.send_max_cool`
- Carlo Milano capture checksum validation.
- Raw Home Assistant infrared timing generation based on the measured Carlo
  Milano captures.
- Internal decode helpers for future receiver-side state sync.
- Config-entry loading with YAML import, matching the Home Assistant 2026.6+
  loading pattern used by the current Z906 reference integration.
- No receiver-side state sync yet. v0.1 is intentionally optimistic because IR
  is one-way until listener support is added.

## Climate Entity

The integration creates one assumed-state climate entity when it is configured
through the UI or YAML import. It sends full captured-style IR states through the
configured `infrared.*` transmitter.

The bundled entity picture is served by the integration at
`/carlo_milano_ir/picon.png` and is also included as `docs/picon.png` for GitHub
use. Additional GitHub documentation artwork is kept in `docs/hero.png` and
`docs/product.png`.

Supported in v0.1:

- HVAC modes: `off`, `cool`, `dry`, `fan_only`, `auto`
- target temperature: 17-30 C in 1 C steps
- fan modes: low, medium, high
- vertical swing: off/on
- turn on restores the last assumed non-off mode

Captured constraints are enforced:

- `dry` is fixed to fan low.
- `auto` and `fan_only` are fixed to fan high.
- The entity is optimistic; if the original remote or front panel is used, Home
  Assistant will not know until receiver-side sync is implemented.

## Artwork

- `docs/hero.png`: GitHub README hero image.
- `docs/product.png`: neutral product-style documentation image.
- `docs/picon.png`: GitHub copy of the climate entity picture.
- `custom_components/carlo_milano_ir/picon.png`: bundled Home Assistant entity
  picture served by the integration.
- `custom_components/carlo_milano_ir/brand/icon.png`: HACS brand icon.

## Protocol Notes

Primary source: captured Carlo Milano NX-7532-675 / REV1_2016 frames.

Detailed research notes:

- [Compatibility and white-label research](docs/compatibility.md)
- [Protocol research notes](docs/protocol-research.md)

Confirmed from captures:

- 38 kHz carrier
- 9 bytes / 72 bits
- MSB-first sending
- header mark/space: `12000 / 5130` us
- bit mark: `550` us
- one space: `1950` us
- zero space: `500` us
- footer mark: `550` us
- repeat gap: `100000` us
- checksum: byte 8 is the sum of bytes 0 through 7 modulo 256

Compatibility cross-check only: IRremoteESP8266 currently has an implementation
named `TROTEC_3550` whose timing constants and state layout match the captured
Carlo Milano frames closely. The integration does not assert manufacturer or OEM
origin from that name. The visually similar Trotec PAC 2100/2600 X product
family should not be treated as a confirmed hardware twin of the Carlo Milano
NX-7532.

The Carlo Milano manual `NX7532_11_158208.pdf` confirms the unit as
`NX-7532-675`, PEARL/Carlo Milano, manual revision `REV1 - 04.01.2017`. It
documents the remote buttons `POWER`, `MODE`, `FAN`, `SWING`, `TIMER`, unit
toggle, up/down, and child lock. It also documents four operating modes:
`AUTO`, `COOL`, `FAN`, and `DRY`.

For generated `send_state` frames, v0.1 only exposes fields that are both
captured and safe to encode: power, cool/off, 17-30 C, fan low/mid/high,
vertical swing, the captured mode cycle, and the captured timer hours. The Carlo
Milano manual documents the COOL setpoint range as 17-30 C, so the Home
Assistant service validates against 17-30 C.

For v0.1, generated states use byte 7 as `0x88`. The confirmed working
17 C / Fan High / Swing Off / Power On frame is
`55 12 00 04 00 00 31 88 24`. Earlier captures included `0x80` and `0xC0` in
byte 7; the meaning of those variants is not yet asserted here.

Fahrenheit display mode is captured for COOL, Fan High, Swing Off, Power On from
86 F down to 62 F. In these frames, byte 7 is `0x40`, byte 3 is the Fahrenheit
offset from 59 F, and byte 1 carries the rounded Celsius-equivalent setpoint
plus the power bit:

```text
86 F: 55 E2 00 1B 00 00 31 40 C3
85 F: 55 D2 00 1A 00 00 31 40 B2
84 F: 55 D2 00 19 00 00 31 40 B1
83 F: 55 C2 00 18 00 00 31 40 A0
82 F: 55 C2 00 17 00 00 31 40 9F
81 F: 55 B2 00 16 00 00 31 40 8E
80 F: 55 B2 00 15 00 00 31 40 8D
79 F: 55 A2 00 14 00 00 31 40 7C
78 F: 55 A2 00 13 00 00 31 40 7B
77 F: 55 92 00 12 00 00 31 40 6A
76 F: 55 82 00 11 00 00 31 40 59
75 F: 55 82 00 10 00 00 31 40 58
74 F: 55 72 00 0F 00 00 31 40 47
73 F: 55 72 00 0E 00 00 31 40 46
72 F: 55 62 00 0D 00 00 31 40 35
71 F: 55 62 00 0C 00 00 31 40 34
70 F: 55 52 00 0B 00 00 31 40 23
69 F: 55 52 00 0A 00 00 31 40 22
68 F: 55 42 00 09 00 00 31 40 11
67 F: 55 32 00 08 00 00 31 40 00
66 F: 55 32 00 07 00 00 31 40 FF
65 F: 55 22 00 06 00 00 31 40 EE
64 F: 55 22 00 05 00 00 31 40 ED
63 F: 55 12 00 04 00 00 31 40 DC
62 F: 55 12 00 03 00 00 31 40 DB
```

Generated Fahrenheit states support `temperature_unit: fahrenheit` with
`temperature` from `62` to `86`. Fahrenheit combined with `timer_hours` is not
generated yet because that combination has not been captured.

Timer captures show a separate selected-timer variant. Pressing `TIMER` can send
a display/entry frame such as `55 1A 11 04 00 00 31 83 38`. The selected-hour
frames use byte 7 `0x82` and byte 2 as the direct hour value from `0` to `24`:

```text
 0 h: 55 1A 00 04 00 00 31 82 26
 1 h: 55 1A 01 04 00 00 31 82 27
 2 h: 55 1A 02 04 00 00 31 82 28
 3 h: 55 1A 03 04 00 00 31 82 29
 4 h: 55 1A 04 04 00 00 31 82 2A
 5 h: 55 1A 05 04 00 00 31 82 2B
 6 h: 55 1A 06 04 00 00 31 82 2C
 7 h: 55 1A 07 04 00 00 31 82 2D
 8 h: 55 1A 08 04 00 00 31 82 2E
 9 h: 55 1A 09 04 00 00 31 82 2F
10 h: 55 1A 0A 04 00 00 31 82 30
11 h: 55 1A 0B 04 00 00 31 82 31
12 h: 55 1A 0C 04 00 00 31 82 32
13 h: 55 1A 0D 04 00 00 31 82 33
14 h: 55 1A 0E 04 00 00 31 82 34
15 h: 55 1A 0F 04 00 00 31 82 35
16 h: 55 1A 10 04 00 00 31 82 36
17 h: 55 1A 11 04 00 00 31 82 37
18 h: 55 1A 12 04 00 00 31 82 38
19 h: 55 1A 13 04 00 00 31 82 39
20 h: 55 1A 14 04 00 00 31 82 3A
21 h: 55 1A 15 04 00 00 31 82 3B
22 h: 55 1A 16 04 00 00 31 82 3C
23 h: 55 1A 17 04 00 00 31 82 3D
24 h: 55 1A 18 04 00 00 31 82 3E
```

The generated `timer_hours` option therefore accepts the fully captured range
`0-24`.

The captured `MODE` cycle, starting from `Cool`, is:

```text
Cool -> Fan -> Dry -> Auto -> Cool
```

Only byte 6 changes during this cycle:

```text
Fan:  55 12 00 04 00 00 33 80 1E
Dry:  55 12 00 04 00 00 12 80 FD
Auto: 55 12 00 04 00 00 30 80 1B
Cool: 55 12 00 04 00 00 31 80 1C
```

This maps byte 6 as `fan << 4 | mode` with `auto=0`, `cool=1`, `dry=2`, and
`fan_only=3`. To avoid inventing codes, generated `send_state` currently allows
all captured `cool` fan speeds, requires `dry` with `fan: low`, and requires
`auto`/`fan_only` with `fan: high`.

`send_max_cool` is a convenience action for the strongest confirmed
remote-sendable cooling state: Cool, 17 C, Fan High, Power On. It deliberately
does not claim to activate the panel-only Super-Kuehlung function from the
manual; that behavior needs a separate power-meter comparison before it can be
treated as identical.

Related-platform research points to an electriQ Compact / COMPACT-V2 9000 BTU
white-label family as a more plausible physical platform candidate than Trotec:
compact cube body, top outlet, 9000 BTU / 2.6 kW class, and matching remote
button layout have been reported. Until a public manual, type plate, or OEM
document is archived with this repository, the integration keeps the protocol
Carlo-Milano-first and does not name a Chinese manufacturer.

## Installation

Copy this repository into Home Assistant as a custom integration, or install it
through HACS once published.

### HACS

When the repository is available in your HACS installation, search for
**Carlo Milano NX-7532 IR** under HACS integrations, download it, and restart
Home Assistant.

For custom-repository installation, add:

```text
https://github.com/mastertape/carlo-milano-ir
```

as an integration repository in HACS.

After installation, restart Home Assistant. Then add the integration from:

Settings -> Devices & services -> Add integration -> Carlo Milano NX-7532 IR

The integration also supports importing an existing YAML marker such as:

```yaml
carlo_milano_ir:
```

For new installs, the UI setup is preferred.

## Services

### Send Known Hex Frame

```yaml
action: carlo_milano_ir.send_hex
data:
  entity_id: infrared.xiao_smart_ir_mate_ir_proxy_transmitter
  code: "55 D2 00 19 00 00 31 88 F9"
```

Expected meaning from captures: Cool, 29 C, Fan High, Swing Off, Power On.

### Send Off Test Frame

```yaml
action: carlo_milano_ir.send_hex
data:
  entity_id: infrared.xiao_smart_ir_mate_ir_proxy_transmitter
  code: "55 70 00 0E 00 00 31 88 8C"
```

### Build A State

```yaml
action: carlo_milano_ir.send_state
data:
  entity_id: infrared.xiao_smart_ir_mate_ir_proxy_transmitter
  power: true
  mode: cool
  temperature: 29
  temperature_unit: celsius
  fan: high
  swing: false
```

Supported modes:

```text
auto
cool
dry
fan_only
off
```

This generates:

```text
55 D2 00 19 00 00 31 88 F9
```

### Build A Fahrenheit State

```yaml
action: carlo_milano_ir.send_state
data:
  entity_id: infrared.xiao_smart_ir_mate_ir_proxy_transmitter
  power: true
  mode: cool
  temperature: 62
  temperature_unit: fahrenheit
  fan: high
  swing: false
```

This generates:

```text
55 12 00 03 00 00 31 40 DB
```

### Build A Timer State

```yaml
action: carlo_milano_ir.send_state
data:
  entity_id: infrared.xiao_smart_ir_mate_ir_proxy_transmitter
  power: true
  mode: cool
  temperature: 17
  fan: high
  swing: false
  timer_hours: 18
```

This generates the captured selected-timer frame:

```text
55 1A 12 04 00 00 31 82 38
```

### Send Max Cool

```yaml
action: carlo_milano_ir.send_max_cool
data:
  entity_id: infrared.xiao_smart_ir_mate_ir_proxy_transmitter
  swing: false
```

This sends the confirmed remote-sendable maximum cooling state:

```text
55 12 00 04 00 00 31 88 24
```

## Safety

This integration does not send anything by itself. It only transmits when a
Home Assistant service action is explicitly called.

Home Assistant 2026.6 added infrared receiver support. The current Home
Assistant infrared API exposes receiver subscription via `async_subscribe_receiver`
and provides received raw timings through `InfraredReceivedSignal`. This v0.1
integration includes local decode helpers for Carlo Milano frames, but it does
not yet create a receiver-bound entity. Receiver-based remote-control state sync
is planned for a later climate-entity version.

## Development Scope

The existing Logitech Z906 integration was used only as an architectural
reference for Home Assistant infrared service registration. It is not modified
or required.

## License And Trademarks

This project is licensed under the Apache License 2.0.

Carlo Milano, PEARL, electriQ, Trotec, and other product or brand names are
trademarks of their respective owners. This project is independent and is not
affiliated with, sponsored by, or endorsed by those trademark owners.

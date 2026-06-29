<h1>
  <img src="docs/picon.png" alt="Smiling Compact 9000 BTU AC" width="42" />
  Compact 9000 BTU IR for Home Assistant
</h1>

![Compact 9000 BTU IR](docs/hero.png)

Home Assistant custom integration that adds a Compact 9000 BTU assumed-state
climate entity and the `compact_9000_btu_ir` service domain for portable air
conditioners controlled through Home Assistant's `infrared` entity platform.

The confirmed test device is a PEARL / Carlo Milano NX-7532-675 with REV1_2016
remote. The project is named around the broader Compact 9000 BTU white-label
platform so owners can find it even when their unit is branded differently.
Search and compatibility terms intentionally include Carlo Milano, PEARL,
electriQ Compact 9000 BTU / COMPACT-V2, and the `TROTEC_3550` protocol name
used by IRremoteESP8266.

[![Open your Home Assistant instance and open this repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=mastertape&repository=compact-9000-btu-ir&category=integration)

## Design Goal

This integration keeps the air-conditioner protocol knowledge in Home Assistant:

1. A compatible IR blaster exposes a Home Assistant `infrared.*` transmitter.
2. Compact 9000 BTU IR builds the IR frames.
3. Home Assistant sends those frames through the configured infrared entity.

It does not add AC-specific buttons to ESPHome YAML and does not
require a dedicated ESPHome action for each air-conditioner command.

The protocol implementation is based on reverse-engineered Carlo Milano
NX-7532-675 / REV1_2016 captures and is exposed under a broader Compact 9000
BTU name. IRremoteESP8266's `TROTEC_3550` implementation is used as a protocol
compatibility cross-check for timing and bit-field hypotheses. This does not
claim that Trotec is the manufacturer or origin of the tested Carlo Milano unit
or of the wider white-label platform.

## Mission

The goal is to make compact 9000 BTU white-label portable AC units usable like
normal Home Assistant climate devices, without moving device-specific AC logic
into ESPHome.

This project should stay:

- beginner-friendly for people who just want to flash an IR proxy, install a
  HACS custom repository, and add a climate entity
- useful for HomeKit, Alexa, and Google Home through normal Home Assistant
  climate semantics
- transparent for the community, with captured frames, decoding notes, and
  compatibility evidence documented instead of hidden in private notes
- conservative about protocol claims: no invented codes, no manufacturer claims
  without sources, and no “looks similar” compatibility without captures

## Requirements

- Home Assistant with the `infrared` platform.
- Any compatible `infrared.*` transmitter entity.
- Tested reference emitter:
  `infrared.xiao_smart_ir_mate_ir_proxy_transmitter`.

No AC-specific ESPHome YAML changes or device-specific ESPHome services are
required by this integration. If you already have a working Home Assistant
`infrared.*` transmitter entity, the integration can use it directly.

## IR Hardware

This integration is transport-agnostic. It does not know or care whether the IR
emitter is a Seeed device, another ESPHome proxy, or a future Home Assistant
infrared emitter. The only hardware contract is a Home Assistant entity in the
`infrared` domain that can transmit commands.

The tested reference emitter is a Seeed Studio XIAO IR Mate flashed with the
official ESPHome IR/RF proxy firmware. ESPHome lists the XIAO IR Mate on its
official [Ready-Made Projects](https://esphome.io/projects/?type=irrf) page
under `Infrared & radio frequency proxy`. To reproduce the tested setup, open
that page, choose `Infrared & radio frequency proxy`, pick `XIAO IR Mate`, and
press `Connect` with the device attached to your computer. The page then flashes
the ready-made ESPHome proxy firmware directly in the browser. After flashing,
the resulting device can be adopted in the ESPHome dashboard. This firmware is
important: the XIAO IR Mate does not ship from the factory with this Home
Assistant infrared proxy firmware already installed.

The recommended firmware source for reproducing the tested setup is the
official
[ESPHome infrared-proxies repository](https://github.com/esphome/infrared-proxies),
which hosts YAML configurations for a curated set of known, tested devices that
can serve as infrared proxies for Home Assistant.

If you maintain the ESPHome configuration manually after adoption, keep the
official IR/RF proxy role intact and verify that Home Assistant exposes an
`infrared.*` transmitter entity for the device. The Compact 9000 BTU commands
belong in this Home Assistant integration, not as one-off AC buttons or custom
actions in ESPHome.

This is different from the older Seeed factory demo firmware with `Signal0` ...
`Signal9`, `Learn`, and `Send` style controls. That factory demo interface is
not enough for this integration. This integration requires the ESPHome IR/RF
proxy firmware, because Home Assistant must see a real `infrared.*` emitter
entity so commands can flow through Home Assistant's official infrared API.

## Compatibility And Confirmation Wanted

Confirmed with local captures:

- PEARL / Carlo Milano NX-7532-675
- REV1_2016 remote
- v0.1 climate control through Home Assistant and HomeKit

Related search targets and candidates that need community confirmation:

- Carlo Milano NX-7532
- Carlo Milano NX-7532-919
- electriQ Compact 9000 BTU
- electriQ COMPACT-V2
- Compact 9000 BTU white-label portable AC units with matching remote layout
- Trotec / TROTEC_3550 protocol-compatible devices, where proven by captures

Please open an issue if you can confirm another brand/model with photos,
manual links, type-plate data, or checksum-valid IR frames. See
[compatibility research](docs/compatibility.md) for the evidence that is most
useful.

## Beginner Setup Overview

The intended beginner path is:

1. Flash a compatible IR proxy such as the Seeed Studio XIAO IR Mate with the
   official ESPHome IR/RF proxy firmware.
2. Adopt the proxy in ESPHome.
3. Verify that Home Assistant shows an `infrared.*` transmitter entity.
4. Install this repository in HACS as a custom integration.
5. Restart Home Assistant.
6. Add **Compact 9000 BTU IR** from Settings -> Devices & services.
7. Select the `infrared.*` transmitter entity.
8. Test with the Climate entity or one of the documented service actions.

The proxy is only the transport. The AC protocol, captures, presets, checksums,
and future receive-side state sync belong in this Home Assistant integration.

## What v0.1 Provides

- A rudimentary assumed-state Climate entity for Home Assistant dashboards,
  automations, and HomeKit bridging.
- A bundled picon/entity picture for the climate entity.
- `compact_9000_btu_ir.send_hex`
- `compact_9000_btu_ir.send_state`
- `compact_9000_btu_ir.send_max_cool`
- Compact 9000 BTU protocol checksum validation.
- Raw Home Assistant infrared timing generation based on the measured Compact 9000 BTU captures.
- Internal decode helpers for future receiver-side state sync.
- Config-entry loading with YAML import, matching the Home Assistant 2026.6+
  custom-integration loading pattern.
- No receiver-side state sync yet. v0.1 is intentionally optimistic because IR
  is one-way until listener support is added.

## Climate Entity

The integration creates one assumed-state climate entity when it is configured
through the UI or YAML import. It sends full captured-style IR states through the
configured `infrared.*` transmitter.

The bundled entity picture is served by the integration at
`/compact_9000_btu_ir/picon.png` and is also included as `docs/picon.png` for GitHub
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
- `custom_components/compact_9000_btu_ir/picon.png`: bundled Home Assistant entity
  picture served by the integration.
- `custom_components/compact_9000_btu_ir/brand/icon.png`: HACS brand icon.

## Protocol Notes

Primary source: captured Carlo Milano NX-7532-675 / REV1_2016 frames.

Detailed research notes:

- [Compatibility and white-label research](docs/compatibility.md)
- [Protocol research notes](docs/protocol-research.md)
- [Community capture and decoding guide](docs/community-captures.md)
- [Roadmap](docs/roadmap.md)

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

Compatibility cross-check: IRremoteESP8266 currently has an implementation
named `TROTEC_3550` whose timing constants and state layout match the captured
Compact 9000 BTU frames closely. This repository therefore keeps Trotec and
`TROTEC_3550` visible in the README and compatibility notes for search and
protocol archaeology. It does not assert manufacturer or OEM origin from that
name. The visually similar Trotec PAC 2100/2600 X product family should not be
treated as a confirmed physical hardware twin of the tested Carlo Milano
NX-7532 without matching captures or documentation.

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

Related-platform research currently points to an electriQ Compact / COMPACT-V2
9000 BTU white-label family as a plausible physical platform candidate:
compact cube body, top outlet, 9000 BTU / 2.6 kW class, and matching remote
button layout have been reported. The Trotec link remains important on the
protocol side because of `TROTEC_3550`, but Trotec hardware compatibility is
not treated as confirmed until a public manual, type plate, or checksum-valid
capture is archived with this repository. The project does not name a Chinese
manufacturer without evidence.

## Installation

Install this repository through HACS as a custom repository, or copy it into
Home Assistant manually as a custom integration.

### HACS

This repository is prepared for HACS and currently installs as a custom
repository. In HACS:

1. Open HACS.
2. Go to `Integrations`.
3. Open the three-dot menu in the top right.
4. Select `Custom repositories`.
5. Add this repository URL:

   ```text
   https://github.com/mastertape/compact-9000-btu-ir
   ```

6. Select category `Integration`.
7. Download `Compact 9000 BTU IR`.
8. Restart Home Assistant.

When the project is accepted into the HACS default repository list, it should
also be discoverable by searching for **Compact 9000 BTU IR**, **Carlo Milano**,
**electriQ Compact**, or related compatibility terms in HACS.

### HACS Publication Status

Current in-repository status:

- HACS metadata is present in `hacs.json`.
- The integration manifest includes the HACS-required metadata keys.
- HACS validation and Hassfest GitHub Actions are included and passing.
- Local brand images are included in
  `custom_components/compact_9000_btu_ir/brand/`.
- Versioned GitHub releases should be used for installs and updates.
- The repository is not yet in the HACS default repository list; use the custom
  repository installation flow above for now.

Note: Home Assistant 2026.3+ supports local brand images for custom
integrations. The icon may still appear as `icon not available` in some HACS
repository overview lists if that view uses the older
`brands.home-assistant.io` CDN path instead of Home Assistant's local brands
API. The integration itself ships local brand assets, and Home Assistant can use
them in contexts that read the local brand folder.

After installation, restart Home Assistant. Then add the integration from:

Settings -> Devices & services -> Add integration -> Compact 9000 BTU IR

The integration also supports importing an existing YAML marker such as:

```yaml
compact_9000_btu_ir:
```

For new installs, the UI setup is preferred.

## Services

### Send Known Hex Frame

```yaml
action: compact_9000_btu_ir.send_hex
data:
  entity_id: infrared.xiao_smart_ir_mate_ir_proxy_transmitter
  code: "55 D2 00 19 00 00 31 88 F9"
```

Expected meaning from captures: Cool, 29 C, Fan High, Swing Off, Power On.

### Send Off Test Frame

```yaml
action: compact_9000_btu_ir.send_hex
data:
  entity_id: infrared.xiao_smart_ir_mate_ir_proxy_transmitter
  code: "55 70 00 0E 00 00 31 88 8C"
```

### Build A State

```yaml
action: compact_9000_btu_ir.send_state
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
action: compact_9000_btu_ir.send_state
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
action: compact_9000_btu_ir.send_state
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
action: compact_9000_btu_ir.send_max_cool
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
integration includes local decode helpers for Compact 9000 BTU frames, but it does
not yet create a receiver-bound entity. Receiver-based remote-control state sync
is planned for a later climate-entity version.

## Roadmap

See [docs/roadmap.md](docs/roadmap.md) for planned follow-up work around
improved Climate behavior, HomeKit/Alexa/Google Home friendliness, Max Cool,
Sleep mode, and future IR receiver state synchronization.

## Development Scope

This project is a Home Assistant consumer of the official `infrared` entity
platform. ESPHome IR/RF proxy devices should remain generic transport emitters
and receivers; model-specific Compact 9000 BTU behavior belongs here.

## Tests

The file `tests/test_compact_9000_btu_ir.py` is a small developer test suite
for the reverse-engineered protocol helpers. It is not loaded by Home Assistant
and is not part of the runtime integration.

The tests protect the captured protocol behavior while the project evolves.
They currently cover:

- 9-byte hex frame parsing and checksum validation
- Celsius and Fahrenheit state generation
- mode, fan, swing, and timer encoding
- raw timing generation for Home Assistant infrared sends
- decoding helpers for future receiver-side state sync

They can be run locally with:

```bash
python3 tests/test_compact_9000_btu_ir.py
```

## License And Trademarks

This project is licensed under the Apache License 2.0.

Carlo Milano, PEARL, electriQ, Trotec, and other product or brand names are
trademarks of their respective owners. This project is independent and is not
affiliated with, sponsored by, or endorsed by those trademark owners.

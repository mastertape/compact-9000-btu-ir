# Changelog

All notable changes to this project will be documented in this file.

This project follows a simple Keep a Changelog-style format.

## [Unreleased]

### Documentation

- Explained the purpose of `tests/test_compact_9000_btu_ir.py` in the README.

## [0.2.2] - 2026-06-29

### Fixed

- Rebuilt the smiling Compact 9000 BTU picon from a clean source image so the
  checkerboard background is no longer baked into the PNG.
- Kept the picon small in the GitHub README heading instead of rendering it as a
  large standalone image.
- Updated the bundled entity picon and local HACS brand icon with real alpha
  transparency.

### Unchanged

- No runtime behavior changed.

## [0.2.1] - 2026-06-29

### Documentation

- Added the smiling Compact 9000 BTU picon to the GitHub README heading.
- Restored real transparency for the bundled picon PNG.

### Unchanged

- No runtime behavior changed.

## [0.2.0] - 2026-06-29

### Documentation

- Added XIAO IR Mate / ESPHome IR/RF proxy setup notes to the README.
- Clarified that the integration targets any compatible Home Assistant
  `infrared.*` emitter, while the XIAO IR Mate is the tested reference setup.
- Documented that the Seeed factory/demo firmware is not enough because Home
  Assistant must expose a real `infrared.*` transmitter entity.
- Added the current HACS publication status and custom-repository installation
  flow.
- Added a roadmap for improved climate control, HomeKit/Alexa/Google Home
  friendliness, Max Cool/Sleep follow-up work, and future IR receiver state
  synchronization.
- Added a beginner-friendly mission/setup overview and community capture guide.
- Moved the public roadmap into `docs/roadmap.md` and linked decoding guidance
  from the README.

### Changed

- Renamed the Home Assistant integration domain from `carlo_milano_ir` to
  `compact_9000_btu_ir`.
- Renamed the custom integration folder and service examples to
  `custom_components/compact_9000_btu_ir` and `compact_9000_btu_ir.*`.
- Removed the public README reference to the internal architecture reference
  project.

### Breaking

- Existing test installs using `carlo_milano_ir.*` services or YAML markers must
  remove the old custom integration/config entry and reinstall this repository
  as `compact_9000_btu_ir`.

## [0.1.1] - 2026-06-29

### Changed

- Renamed the public project and HACS display name to `Compact 9000 BTU IR`.
- Reworded README and compatibility text so Carlo Milano / PEARL remains the
  confirmed test device, while electriQ Compact, COMPACT-V2, Compact 9000 BTU
  white-label units, and `TROTEC_3550` protocol-compatible devices are visible
  as search and confirmation targets.
- Kept the original technical Home Assistant domain unchanged for compatibility
  with existing test installs. This was superseded in the 0.2.0 domain rename
  above.

## [0.1.0] - 2026-06-29

### Added

- Added the initial `carlo_milano_ir` Home Assistant custom integration.
- Added `send_hex` for validated 9-byte Compact 9000 BTU IR frames.
- Added `send_state` for captured power, mode, temperature, fan, swing, and
  timer fields.
- Added `send_max_cool` as a convenience action for Cool, 17 C, Fan High,
  Power On.
- Added a rudimentary assumed-state Climate entity for Home Assistant
  dashboards, automations, and HomeKit bridging.
- Added a bundled picon/entity picture, also shown in the GitHub README.
- Added a HACS brand icon under the integration's `brand` directory.
- Added Celsius 17-30 C and Fahrenheit 62-86 F state generation from captured
  frames.
- Added timer generation for the captured 0-24 hour range.
- Added decode helpers for 9-byte frames and raw timings as groundwork for
  future receiver-side state sync.
- Added HACS and Hassfest GitHub Actions workflows.
- Added compatibility and protocol research documentation for Carlo Milano,
  PEARL, electriQ Compact, Compact 9000 BTU, and `TROTEC_3550` search terms.
- Updated the public display name to `Compact 9000 BTU IR` for
  better HACS and GitHub discoverability.

### Notes

- The first implementation is based on Carlo Milano / PEARL captures and does
  not claim Trotec hardware origin. IRremoteESP8266's `TROTEC_3550` name is
  treated as a protocol compatibility cross-check and search term.
- The Climate entity is optimistic in this release. Receiver-side state sync,
  presets, sleep investigation, and panel-only special modes are deferred.
- Basic climate control has been confirmed working in Home Assistant and
  HomeKit on the tested Carlo Milano NX-7532-675 setup.

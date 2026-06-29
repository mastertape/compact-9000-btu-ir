# Changelog

All notable changes to this project will be documented in this file.

This project follows a simple Keep a Changelog-style format.

## [0.1.0] - 2026-06-29

### Added

- Added the initial `carlo_milano_ir` Home Assistant custom integration.
- Added `send_hex` for validated 9-byte Carlo Milano NX-7532 IR frames.
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
- Updated the public display name to `Carlo Milano Compact 9000 BTU IR` for
  better HACS and GitHub discoverability.

### Notes

- The integration is Carlo-Milano-first and does not claim Trotec hardware
  origin. IRremoteESP8266's `TROTEC_3550` name is treated only as a protocol
  compatibility cross-check.
- The Climate entity is optimistic in this release. Receiver-side state sync,
  presets, sleep investigation, and panel-only special modes are deferred.
- Basic climate control has been confirmed working in Home Assistant and
  HomeKit on the tested Carlo Milano NX-7532-675 setup.

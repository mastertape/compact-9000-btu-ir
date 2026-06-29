# Community Capture And Decoding Guide

This project is built from real IR captures. Community reports are most useful
when they include enough evidence to compare protocol, hardware, and remote
behavior without guessing.

## What To Submit

Please open a GitHub issue with:

- brand and exact model number
- photos of the unit, type plate, and remote
- manual PDF or public product/manual link
- remote markings such as `REV1_2016`
- Home Assistant / ESPHome proxy hardware used for capture
- raw timings or decoded 9-byte frames
- what the unit display showed before and after each button press

## High-Value Captures

If you can capture only a few commands, prioritize:

- power on and power off
- cool 17 C, fan high, swing off
- cool 29 C, fan low/mid/high
- swing off/on
- mode cycle: cool -> fan -> dry -> auto -> cool
- Celsius/Fahrenheit toggle
- timer entry and timer values 0-24 h
- any panel-only functions such as Max Cool or Sleep, if the unit emits IR or
  changes behavior after the original remote is used

## Frame Format Used Here

Known matching frames are 9 bytes / 72 bits, MSB-first, with checksum byte 8 as
the sum of bytes 0 through 7 modulo 256.

Example:

```text
55 12 00 04 00 00 31 88 24
```

That frame is the confirmed remote-sendable maximum cooling state on the tested
PEARL / Carlo Milano NX-7532-675: Cool, 17 C, Fan High, Swing Off, Power On.

## Helpful Related Projects

- Home Assistant's `infrared` entity platform provides the transport API this
  integration uses.
- ESPHome's `infrared-proxies` project provides ready-made firmware for generic
  IR/RF proxy devices such as the XIAO IR Mate.
- IRremoteESP8266 contains the compatible protocol name `TROTEC_3550`, which is
  useful for protocol archaeology. This project does not treat that name as a
  manufacturer or hardware-origin claim.

## Evidence Rules

Please avoid compatibility claims based only on similar product photos. The
most useful evidence is one of:

- checksum-valid matching frame
- matching remote and manual
- matching type-plate/product family plus captures
- repeatable behavior on real hardware


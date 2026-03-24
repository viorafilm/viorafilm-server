## Goal

Move layout geometry from asset inference into explicit layout metadata, while
keeping the current production behavior available as a fallback until each
layout is verified on hardware.

## Why

Current behavior is mostly correct, but some kiosks break because users replace
frame assets and the app infers photo slots from those PNGs.

That means:

- the same build can print differently on different kiosks
- `showing_select_Frame` and `Frame2` assets can accidentally affect geometry
- a frame design change can alter slot detection even if the user only meant
  to change decoration

## Important constraint

Do not repeat the earlier "canonical fixed coordinates in code" approach.

That failed because the coordinates were forced globally in code and did not
respect per-kiosk asset differences.

The new approach must be:

- external metadata, not hardcoded geometry in Python
- staged rollout, not all layouts at once
- `meta -> current inference -> fallback` during migration

## Intended model

### Preview assets

`showing_select_Frame` should be preview-only.

It should not be used to infer slot geometry.

### Print assets

`Frame1` and `Frame2` stay as print layers:

- `Frame1` = bottom layer
- photo slots = inserted between layers
- `Frame2` = top overlay

### Metadata

Create layout metadata files, one per layout family.

Suggested location:

- `assets/layout_meta/2641.json`
- `assets/layout_meta/6241.json`
- `assets/layout_meta/4641.json`
- `assets/layout_meta/4661.json`
- `assets/layout_meta/4681.json`
- `assets/layout_meta/2461.json`

Suggested fields:

- `preview_canvas_size`
- `print_canvas_size`
- `preview_slots`
- `print_slots`
- `qr_preview_rect`
- `qr_print_rect`
- `copies_per_page`
- `grouping`
- `inherits`
- `asset_family`

## Migration order

### Phase 1

Convert `2641` and `2461` first.

Reason:

- `2461` behaves like the `2641` family
- celebrity mode can inherit geometry from `2641`
- this is the safest first slice

### Phase 2

Convert `6241`.

Reason:

- strip grouping and QR placement are special
- this is the layout that most often shows split/QR issues

### Phase 3

Convert `4641`, `4661`, and `4681`.

Reason:

- these share similar vertical multi-slot behavior
- they can reuse the same migration shape once the first families are stable

## Celebrity mode

`2461` should not get a separate geometry engine.

Use:

- metadata inheritance from `2641`
- separate celebrity asset roots only for assets
- existing celebrity capture overlay flow unchanged

## Runtime rules during migration

For each layout:

1. if metadata exists, use metadata
2. else use current inference path
3. if inference fails, use existing fallback

Add logs so we always know which path was used:

- `layout meta hit`
- `layout legacy detect hit`
- `layout fallback hit`

## Safety rules

- do not change printer model routing during this refactor
- do not remove legacy inference until hardware verification is complete
- do not change all layouts in one patch
- compare preview and print output against the current good baseline before
  expanding

## Expected result

- users can replace frame art without changing photo geometry
- `showing_select_Frame` is used only for fast preview display
- slot detection is no longer affected by arbitrary PNG edits
- per-layout behavior becomes stable across kiosks

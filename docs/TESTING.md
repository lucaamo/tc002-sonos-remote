# Testing and release checklist

## Repository checks

Run from the repository root:

```sh
python3 -m unittest discover -s tests -v
git diff --check
```

The tests protect the public MQTT contract, the Berry app metadata, the
required license notice, the optional-icon fallback, and the absence of known
private device identifiers.

## Berry compile and framebuffer

Install the complete script and inspect the compiler result:

```sh
curl -fsS -X PUT "http://AWTRIX_IP/api/v1/apps/script/sonos_remote" \
  -H 'Content-Type: text/plain' \
  --data-binary @apps/sonos_remote.ax
curl -fsS "http://AWTRIX_IP/api/v1/apps"
```

`sonos_remote` must report `error: null`. Force or enter the app, then read the
52×16 framebuffer:

```sh
curl -fsS "http://AWTRIX_IP/api/v1/display/screen"
```

Confirm the frame is non-black, no text is clipped, the header has access to
the full width, and the title remains clear of the lower icon. The API frame is
useful evidence but does not replace looking at the physical panel.

## Home Assistant checks

1. Confirm MQTT is connected on both Home Assistant and AWTRIX NG.
2. Choose a test Sonos player at a safe volume.
3. Publish `refresh` and confirm the retained player state topics update.
4. Configure two named Playlist fields in the Berry app, enter the remote, rotate between them and
   confirm the highlighted name changes without leaving the app.
5. Select one entry and confirm the player receives its content id and type.
6. Test one short press, one clockwise detent, one counter-clockwise detent, and
   one rocker press.
7. Confirm the rocker changes Sonos volume and leaves the local TC002 speaker
   volume unchanged.
8. Press the rocker repeatedly and confirm the two-second overlay restarts and
   never flashes an older value.
9. Test configured `play_media` with the Home Assistant action tester before
   invoking it from the TC002.
10. Start a track with artwork and confirm that a `16×16` cover fills the left
    side while artist and title remain readable in the 36 columns on the right.
11. Start a source without artwork and confirm that the local Music Meter icon
    or built-in shape fallback appears without a script error.

## Physical global-shortcut checks

1. Wait on a normal carousel app and hold the knob for `long_ms`.
2. Confirm Sonos Remote opens immediately and the carousel stays paused.
3. Exercise all five controls while the remote remains visible.
4. Hold the knob again; confirm the remote exits and the next carousel app
   appears without a reboot or stale input.
5. Power-cycle twice and repeat entry/exit.
6. Verify the firmware port's documented stock/recovery boot gesture still
   works before treating a persistent build as recoverable.

Do not publish a new firmware binary from these checks. The patch in this
repository is source-level reference material only.

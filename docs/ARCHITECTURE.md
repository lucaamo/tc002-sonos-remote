# Architecture and extension guide

## Components

1. **TC002 native input hook** detects a global main-knob hold and opens the
   Berry app. While the app is active it routes rotary and rocker events to the
   script before applying normal carousel or local-volume behaviour.
2. **`apps/sonos_remote.ax`** owns the exclusive display and maps physical
   events to a narrow MQTT protocol. It stores no Home Assistant token or MQTT
   password.
3. **TC002 AWTRIX Bridge** subscribes to the command topic, validates JSON and
   the requested `media_player`, serializes commands with an async lock, calls
   the Home Assistant API, then publishes retained player state.
4. **Home Assistant** provides the Sonos entity and the standard
   `media_player` services.

## MQTT contract

Default root: `tc002/sonos_remote/v2`.

The app publishes JSON to `<root>/command`:

```json
{"action":"play_pause","player_entity_id":"media_player.living_room"}
```

Allowed actions and additional fields are:

| Action | Additional fields |
| --- | --- |
| `refresh` | none |
| `play_pause` | none |
| `next` | none |
| `previous` | none |
| `volume` | `value`, integer `0..100` |
| `delta` | `value`, integer `-25..25` |
| `play_media` | non-empty `media_content_id` and `media_content_type` |

The bridge publishes retained text payloads to:

- `<root>/state/artist`
- `<root>/state/title`
- `<root>/state/playing`
- `<root>/state/volume`
- `<root>/state/player_name`
- `<root>/state/error`
- `<root>/state/playlists` - a JSON array of `{name, mediaContentId,
  mediaContentType}` entries

The bridge rejects unknown actions, invalid volume values, missing content, and
entities that are not valid Home Assistant `media_player` objects.

## Playlist picker

The Home Assistant bridge owns the ordered playlist list and validates a
maximum of twelve uniquely named entries. The Berry app receives the retained
JSON list and opens the picker whenever an inactive session enters Sonos
Remote. Knob rotation changes only the highlighted index while the picker is
open; a short press publishes `play_media` with the selected entry. The picker
times out without starting media and never changes the existing mappings once
the playback view is active.

The bridge keeps the previous single `playlistMediaContentId` and
`playlistMediaContentType` values as a compatibility input. If the new array is
empty, it exposes that pair as one in-memory `Playlist 1` entry.

## Input and exclusive mode

The native hook watches the select button outside `sonos_remote`. After
`long_ms`, it activates the app and consumes the release edge. This avoids a
short-press action immediately after entering the remote.

`on_show()` pauses rotation and marks the app active. While active:

- the official TC002 input topics distinguish short and long select presses,
  rotary movement and the two rocker buttons;
- the picker consumes rotary movement only during its initial selection phase;
- the rocker changes Sonos volume without touching the local speaker;
- `should_show()` returns true only for the active session, keeping the launcher
  out of the normal carousel;
- `exit_mode()` resumes rotation and advances to the next app.

The exit hold is handled in Berry. The native hook deliberately ignores a hold
that begins while `sonos_remote` is current, preventing exit from reopening the
same app.

## Display state

The 52×16 view has two text rows. The artist header is uppercase, white, and
centred across the panel. It scrolls once when necessary, then remains in a
readable resting form. The title is centred in the columns beside the lower
10×10 icon and scrolls when it does not fit.

During a rocker change, the normal view is replaced for two seconds by a Sonos
volume overlay. Every new press restarts that timer. `pending_until` blocks an
older periodic Home Assistant report from replacing the optimistic value for
three seconds; a matching report confirms it early.

## Concurrency rules

- Home Assistant service calls are serialized by the bridge's Sonos controller
  lock. Rapid rocker commands therefore cannot race independent refreshes.
- The app computes the next absolute volume from its optimistic value after the
  first valid state report. Before that, it sends a bounded delta.
- A periodic refresh must not clear the volume overlay or overwrite a pending
  volume with an older state.
- MQTT callbacks hand work back to the asyncio event loop. Rendering and state
  mutation do not run concurrently on the MQTT client thread.
- Command service requests must not append `?return_response`.

## Adding a command

1. Add the physical mapping in the Berry input hook and publish a new explicit
   `action` string. Keep the payload small and do not add credentials.
2. Add the action to the allow-list in the bridge's
   `SonosController.remote_command()`.
3. Validate every new field before calling Home Assistant.
4. Call one specific Home Assistant service without `?return_response`.
5. Refresh and publish state only after the service call completes.
6. Add Berry contract tests, bridge unit tests, and a physical test that checks
   the carousel and local TC002 controls were not affected.

## Adding a setting

Declare user-editable Berry values in a leading `# @config` line, read them
with `store.get()`, and give them a bounded type/range. If the bridge also owns
the setting, extend its settings defaults and validator, its HTTP schema, and
its UI together. Existing installations must retain a safe default.

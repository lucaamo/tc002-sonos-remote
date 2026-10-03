# Test record and release checks

## Hub publication and installation — 2026-10-03

Version 3.3.1 adds author, panel and module dependency metadata and an empty
optional fallback-icon default. Control and artwork logic is unchanged from
3.3.0. The repository suite ran 31 tests: 30 passed and the hardware test was
skipped in that run. The hardware test was then run separately on official
TC002 beta 1.1.6 and passed all 106 actual Berry runtime assertions.

Three original preview images were prepared with example data. The main
preview uses the actual class renderer in a temporary, inert on-demand app;
it sends no player commands. The production app and module sources and
settings were compared before and after and were identical.

The three flows were then published as lucaamo. Sonos Remote declares the
two real module Hub IDs. **Send to AWTRIX** updated the existing app to 3.3.1.
For the missing-dependency trial, the two backed-up Sonos modules were
temporarily removed, with the on-demand session stopped. The main Hub page
identified both missing modules; **Install with dependencies** downloaded
and installed both modules and the main app successfully on official 1.1.6.
All three installed sources matched the repository code after stripping the
generated `@hub` origin line and normalizing trailing newlines. The origin
IDs matched their three public flow pages.

New module defaults were empty. Existing playlist and artist-rule values
were restored from the private backup and compared field by field. The main
app's settings were preserved by the update. All apps reported no errors;
the installed app set, enabled states and carousel positions were unchanged.
CasaViva, sensor carousel, Weather and Aquarium sources/settings were identical.
Sonos Remote was reopened without sending music or volume commands.

The clock-editor **Install all** prompt also recognized both dependency IDs,
but its download needed a Hub connection key in that browser; it installed
nothing. The successful dependency trial used the signed-in Hub page instead.
No connection key was saved. This verifies installation of missing modules
and updating an existing main app, not a factory-reset clock or a new user's
Home Assistant onboarding.

## Native URL artwork on official beta 1.1.6 — 2026-10-03

Sonos Remote 3.3.0 was installed on the official OTA package
`1.1.6-g237da747091b`; the device confirmed the update after its stability
period. JPEG and PNG 256×256 quadrant sources were downloaded from HA and
resized to the entire 16×16 area, with all four corners verified. A 640×640
album JPEG also rendered all sixteen rows. The production HA blueprint then
published a real Sonos proxy URL and the clock drew its 640×640 original
album cover as 16×16 without an external converter. Empty artwork restored
the fallback. Playback source and volume were restored after a silent test.

The actual Berry class passed 106 runtime checks, including HTTP/HTTPS URLs,
malformed/oversized URLs, existing GIF/RGB handling, artists, ten playlist
slots and controls. Ten URL resolution/invalid-input fixtures passed in the
actual HA template engine. No new physical button acceptance was performed.
Device scripts, configurations, icons and carousel order were checked against
private backups; only the intended app sources changed. The separate TC001
and unrelated HA automations/scripts were preserved. The temporary converter
was archived and removed only after native artwork passed on real hardware.

These results use the official firmware's image decoder. They do not certify
the historical C++ proposal under `native-artwork/`.

## GIF artwork on official beta 1.1.5 — 2026-10-02

Version 3.2.3 draws a provider's static 16×16 GIF data URI with native `icon()`.
A four-quadrant probe matched all 256 framebuffer pixels. A real album cover
also matched every pixel after GIF decoding. Empty and malformed GIF payloads
fell back to the icon without Berry errors; legacy RGB rendering still passed.
The actual Berry regression harness passed 96 checks, including existing control
and playlist behavior. No new physical control test was performed for this
artwork-only update. Protected scripts/configuration/rotation stayed unchanged.
The GIF converter is a temporary optional HA-side provider; these checks do not
establish full-size JPEG support or firmware-native image resizing.

## Native artwork source candidate — 2026-10-02

The separate [native candidate](../native-artwork/README.md) has 13 native
test cases using the real C++ implementation, including 40 deterministic
malformed-image mutations. Host tests pass under AddressSanitizer and
UndefinedBehaviorSanitizer on macOS ARM64. Linux sanitizer CI also exercises
the same driver. Tests include progressive/baseline JPEG, PNG alpha/palette/
grayscale, 10×10/16×16, center crop, area resampling, source and streaming-body
bounds, allocation-budget refusal, cache hits, stale and duplicate completions,
size changes, retry and unload invalidation.

A private real-current-album input (83,636 encoded bytes) also converts into
256 RGB888 pixels; decoder payload allocation peak was 2,887,743 bytes on the
host. No album asset, signed URL or user's metadata is committed. This is a
host measurement, not ARMv7 memory/CPU/FPS evidence.

**Not tested or installed on TC002:** native HTTP download adapter, Berry
image bindings, target ARM build, RAM/FPS/input latency and firmware updates.
Matching beta source is needed to finish those checks. Existing Sonos Remote,
HA automation, TC001 and CasaViva were preserved.

## Verified on 2026-10-02

Environment: official TC002 beta AWTRIX NG **1.1.5**, Home Assistant **2026.9.4**.
Public code uses neutral settings; private device snapshots are kept outside the
repository. No firmware was flashed or reset for these checks.

| Check | Evidence / result |
| --- | --- |
| Source/privacy/contract tests | unittest suite; private defaults absent |
| Blueprint protocol validation | 30 fixtures locally; 29 JSON-serializable fixtures rendered in actual HA, all passed |
| Actual Berry execution | 92 assertions, including global artist rules with a 400-entry catalogue, priority overrides, finite/continuous native scroll settings, ten-slot selection and native exit payloads, in temporary headless probe, passed for 3.2.2 |
| Fresh namespace | New app/module identities, empty playlists/artist rules and entity/prefix defaults |
| Independent HA backend | Different Sonos entity, unique MQTT root; existing add-on does not own this root |
| Native registration/launch | API reports ondemand=true; app starts and draws 52×16 text |
| Standalone metadata | New app receives nonempty track title from the blueprint |
| Display ownership | App remains selected beyond global carousel dwell |
| Continuous artist rendering | Isolated on-demand probe observes at least two completed native passes of an unconfigured long artist; 21 smoke checks passed for 3.2.2 |
| Native API exit | Another carousel app becomes active and blockNavigation returns false |
| Actual HA service | MQTT volume command invokes media_player.volume_set at the existing volume; trace finished successfully |
| Invalid incoming commands | Malformed JSON, out-of-range volume and wrong entity abort before services |
| Test cleanup | Temporary scripts/modules and HA automation removed; working production sources/settings retained |

The fresh test is an isolated configuration on the existing clock, **not** a
factory-reset installation, second-device certification or full physical
control acceptance. The service test deliberately keeps the original volume;
it does not start playback or skip the household's track.

## Run repository checks

```sh
python3 -m pip install -r requirements-dev.txt
python3 -m unittest discover -s tests -v
git diff --check
```

Tests cover fixed service routing, input validation, volume bounds/unknown
volume, neutral source defaults, module rules, optional art/icon and notices.
CI runs these without a clock; the hardware-runtime test is skipped there.

## Run actual Berry regression

```sh
AWTRIX_TEST_URL=http://AWTRIX_IP python3 -m unittest tests.test_artist_runtime -v
```

This uploads an isolated module and a headless probe, then removes them in
`finally`. It executes the actual app class using local clock, rendering,
settings, MQTT and rotation fakes. Ninety-two assertions cover artist parsing,
first-pass completion, centring and group scrolling; native select suppression,
button repeat, duplicate MQTT suppression, rotary direction and picker;
optimistic volume and stale echoes; malformed/valid artwork; offline recovery
and hide cleanup. Picker checks cover the exact knob-hold boundary, empty-list
no-op, four-entry and ten-entry wrap, confirmation, cancel, remembered selection, timeout,
metadata updates and volume-overlay dismissal without losing stale-volume
protection. The actual artist module loads one global catalogue exceeding the
old 4,096-character per-list limit, checks its first/last entry and priority
overrides, including keeping a band name whole. The real playlist module loads all ten settings; the production
class confirms the tenth item, handles large positive/negative turns and skips
blank/malformed entries without losing later slots. Exit checks cover
non-retained native exit, duplicate/late input suppression,
bounded retry after a lost command, and reuse after hide. The rotation fake
raises if the unsafe Berry exit path is used. No real media commands are sent
by the harness.

## Fresh-config smoke test

Create a temporary automation from the supplied blueprint, selecting a test
Sonos player and unique root. Then run:

```sh
python3 tools/smoke_ondemand.py --url http://AWTRIX_IP \
  --root test_clock/sonos_remote --player media_player.test_room \
  --device-root YOUR_CLOCK_MQTT_PREFIX
```

The helper refuses to replace existing test names, installs temporary app/module
identities with neutral defaults and verifies twenty-one lifecycle/frame/metadata
checks. It sends only refresh media commands. Timers inject knob holds and a
turn into the production handler, checking picker open, selection, cancellation,
reopening and timeout on the real display. The temporary playlist module has
ten synthetic entries, exercises browsing to the tenth and is never confirmed.
The probe fixes its artist to a long unconfigured band name and checks at least
two completed native scrolling passes. Version 3.2.1 used a finite repeat for
this case, leaving the header offscreen after its first pass. Version 3.2.2
uses unlimited repeats unless a fitting alias is explicitly configured.
It then calls the production `exit_mode()`;
its actual native MQTT command must unload the app. This catches the Berry
exit-path defect that an HTTP-only exit test missed. The helper removes its
scripts in `finally`. It does not reset or replace the
production controller's source or settings. If a controller is already open,
the helper exits it to the normal carousel before launching its isolated app.
It bounds the dwell test to 50 seconds. Remove the
separately created test automation and its retained state topics afterward.
The earlier v3.0.1 helper passed twelve checks, including exit through the then
app-exit knob handler. In 3.1.0 that gesture is intentionally playlist selection.
The revised helper passed all eighteen checks on the same TC002 with 3.1.0.
Its timer chain uses one pending timer at a time and rejects any non-refresh
media command before publication, including an accidental short press caused
by timer scheduling. This bounds test side effects without replacing the
production input handlers or native exit path.

## Physical trial and exit correction in v3.0.1

On the production TC002 the user confirmed playlist browsing and launch,
track next/previous, play/pause, and 2-percentage-point Sonos volume feedback.
The first v3.0 knob exit failed: press/release reached MQTT, but the app reopened.
This was also reproduced by a controlled long-press injection while the app was
absent from the normal carousel. Native MQTT `cmd/apps/next` restored the carousel
and released navigation; v3.0.1 uses that path. The corrected installed app also
passed the same controlled press/release test, without restarting the device.
The user then confirmed real knob-hold exit and carousel resumption, followed
by entry from the firmware menu and the four-playlist picker.
The user also confirmed native top-select-hold exit back to the carousel.

These user confirmations concern the installed private playlist settings;
public source keeps empty playlists and neutral player/prefix defaults.

## Playlist gesture changes in v3.1.0

The knob now owns playback and playlist selection; long top select remains the
local physical exit. Short top select causes no media action. The actual Berry
harness passed 77 checks. After installing 3.1.0 the user confirmed physical
hold-to-open, rotary browsing and another hold cancelling back to music without
launching the highlighted playlist. This is a new acceptance result, separate
from the earlier 3.0.1 hold-to-exit confirmation.
The 3.1.0 upgrade preserved all twelve configured values and the personal
artist-name module; source readback matched the published candidate exactly.

## Ten playlist slots in v3.2.0

The app imports a separate Sonos Playlists module with ten configurable fields,
within the firmware's twelve-field-per-script limit. The actual Berry harness
passed 88 checks and the fresh-config display helper passed twenty checks,
including loading ten module values and browsing to the tenth item. The
temporary entries were never played; probes and their settings were removed.

On the production upgrade, all four existing playlist strings were transferred
unchanged from the app to module slots 1–4; slots 5–10 remain empty. All eight
other app values and the personal artist module were preserved. Both app and
module source readbacks matched the candidate files. The previous 3.1.0 source
and twelve-field configuration are saved privately for rollback. No firmware
or HA automation changes were required. Physical controls are unchanged from
3.1.0; tenth-item selection has automated rather than human acceptance.

## Remaining physical acceptance

These checks still require a person at the device; automated handler execution
is not proof of physical electrical/input timing:

1. Repeat entry from each carousel page using top select → Scripts → Sonos
   Remote; menu entry has passed on the available TC002. Confirm the launching
   gesture does not start music.
2. Browse at least two configured playlists, confirm one with the knob, then
   test play/pause and next/previous on the actual Sonos queue.
3. Press/hold top left/right; confirm Sonos changes and TC002 local speaker
   volume stays unchanged. Confirm the OSD lasts two seconds after the last press.
4. During music hold/release the knob to reopen playlists; rotate and confirm.
   Repeat a hold in the picker to cancel, then verify its inactivity timeout.
   Neither cancel nor timeout may change playback. Exit with top select hold
   and repeat entry/exit cycles.
5. Test MQTT disconnect/reconnect, unavailable Sonos and HA restart. Local
   top-select exit must work without MQTT. After 65 seconds without HA state
   the app requests exit; broker loss delays the MQTT exit until reconnection.
6. Save settings, remove/reinstall the script, and power-cycle twice. Verify
   navigation is restored on unload/error paths and settings persist.
7. Inspect the real panel for clipping and artist behaviour. Actual drawing font
   and alias width must be checked in a drawing frame, not by character count.

Artwork is an optional separate provider: test valid/invalid/no-cover inputs if
using one. The standalone blueprint intentionally provides no image conversion.
No additional firmware patch or beta binary is distributed by this repository.

# Test record and release checks

## Verified on 2026-10-02

Environment: official TC002 beta AWTRIX NG **1.1.5**, Home Assistant **2026.9.4**.
Public code uses neutral settings; private device snapshots are kept outside the
repository. No firmware was flashed or reset for these checks.

| Check | Evidence / result |
| --- | --- |
| Source/privacy/contract tests | unittest suite; private defaults absent |
| Blueprint protocol validation | 30 fixtures locally; 29 JSON-serializable fixtures rendered in actual HA, all passed |
| Actual Berry execution | 46 assertions in temporary headless probe, passed |
| Fresh namespace | New app/module identities, empty playlists/artist rules and entity/prefix defaults |
| Independent HA backend | Different Sonos entity, unique MQTT root; existing add-on does not own this root |
| Native registration/launch | API reports ondemand=true; app starts and draws 52×16 text |
| Standalone metadata | New app receives nonempty track title from the blueprint |
| Display ownership | App remains selected beyond global carousel dwell |
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
settings, MQTT and rotation fakes. Forty-six assertions cover artist parsing,
first-pass completion, centring and group scrolling; native short/long release,
button repeat, duplicate MQTT suppression, rotary direction and picker;
optimistic volume and stale echoes; malformed/valid artwork; offline recovery
and hide cleanup. No real media commands are sent by the harness.

## Fresh-config smoke test

Create a temporary automation from the supplied blueprint, selecting a test
Sonos player and unique root. Then run:

```sh
python3 tools/smoke_ondemand.py --url http://AWTRIX_IP \
  --root test_clock/sonos_remote --player media_player.test_room \
  --device-root YOUR_CLOCK_MQTT_PREFIX
```

The helper refuses to replace existing test names, installs temporary app/module
identities with neutral defaults and verifies twelve lifecycle/frame/metadata
checks. It sends only refresh commands. It exits the remote through the native
API and removes its scripts in `finally`. It does not reset or replace the
production controller. It bounds the dwell test to 50 seconds. Remove the
separately created test automation and its retained state topics afterward.

## Remaining physical acceptance for v3.0

These checks still require a person at the device; automated handler execution
is not proof of physical electrical/input timing:

1. Enter from Time, Casa Viva and another carousel app using top select →
   Scripts → Sonos Remote. Confirm the launching gesture does not start music.
2. Browse at least two configured playlists, confirm one with knob/select, then
   test play/pause and next/previous on the actual Sonos queue.
3. Press/hold top left/right; confirm Sonos changes and TC002 local speaker
   volume stays unchanged. Confirm the OSD lasts two seconds after the last press.
4. Exit by top-select hold and by active-session knob hold; repeat entry/exit.
5. Test MQTT disconnect/reconnect, unavailable Sonos and HA restart. Native exit
   must work without MQTT; after 65 seconds without state the app should exit.
6. Save settings, remove/reinstall the script, and power-cycle twice. Verify
   navigation is restored on unload/error paths and settings persist.
7. Inspect the real panel for clipping and artist behaviour. Actual drawing font
   and alias width must be checked in a drawing frame, not by character count.

Artwork is an optional separate provider: test valid/invalid/no-cover inputs if
using one. The standalone blueprint intentionally provides no image conversion.
No additional firmware patch or beta binary is distributed by this repository.

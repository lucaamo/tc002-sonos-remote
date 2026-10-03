# Sonos Remote for AWTRIX NG on Ulanzi TC002

A reusable Berry controller for one Home Assistant Sonos player. Version 3.3.1
uses AWTRIX NG's official **on-demand** framework and a Home Assistant blueprint.
No TC002 AWTRIX Bridge add-on, private firmware patch, Home Assistant token on
the clock, or author's network configuration is required.

This is a community example, not an app accepted or bundled by Blueforcer.
Tested with official TC002 beta **AWTRIX NG 1.1.6** and Home Assistant **2026.9.4**.
Other firmware versions and TC001 are not verified. See
[acceptance results and remaining checks](docs/TESTING.md) and
[upstream readiness](docs/UPSTREAM_READINESS.md).

For the clock app and module dependency packaging, see
[AWTRIX Hub distribution](docs/HUB_DISTRIBUTION.md). Home Assistant setup is
separate from installing the Berry files on the clock.

Official beta 1.1.6 downloads and resizes artwork URLs itself. The older
[native artwork conversion candidate](native-artwork/README.md) is retained
as a historical proposal; no firmware patch is needed for this artwork path.

## Controls and a beta limitation

From any carousel page, **hold the top middle/select button for one second**,
choose **Scripts**, then **Sonos Remote**. The firmware suspends the carousel.
The web UI's **Start** button also launches it.

| While Sonos Remote is running | Action |
| --- | --- |
| Rotate the knob in the playlist picker | Choose one of up to ten configured playlists/favourites |
| Short knob press | Start the highlighted item; otherwise play/pause |
| Rotate clockwise / counter-clockwise after picker | Next / previous track |
| Top right / left button | Increase / decrease Sonos volume |
| Hold a volume button | Repeat volume changes |
| Hold top select for one second | Firmware exits and restores the carousel |
| Hold knob for configured duration, then release | Open the playlist picker; repeat to cancel and return to music |
| Short top select press | No music action; this button is reserved for firmware exit |

The picker opens on entry when playlists are configured. During playback, a
knob hold reopens it at the last highlighted item in this session. Confirmation
starts that item and returns to now playing. Cancel or timeout (eight seconds
by default) returns to music without changing playback. With no configured
playlists, a knob hold has no effect. Opening the picker dismisses an existing
volume overlay so the choice is immediately visible.

**Entry by holding the knob from anywhere is not part of this native adapter.**
The beta routes the three top buttons to scripts locally; it exposes knob events
only through MQTT. The app subscribes to the knob only during an on-demand
session. It uses `blockNavigation` then to suppress the clock's local
brightness/volume panel. Sonos volume and the TC002 speaker remain separate.
No hidden global listener or firmware constant is required.

Top-select hold exits locally even when MQTT is unavailable. The backend-loss
failsafe uses the clock's native MQTT `cmd/apps/next` command on beta 1.1.5:
`rotation.next()` inside this on-demand app reopened it during the physical
trial. The knob controls music and playlists; it no longer exits the app.

The old global MQTT entry prototype is preserved in
[`compatibility/sonos_remote_mqtt_v2.ax`](compatibility/sonos_remote_mqtt_v2.ax).
Do not run both controllers together. The old
[`patches/`](patches/) directory is historical source-only material, not an
installation instruction for the official beta.

Official API references: [on-demand lifecycle](https://ang.blueforcer.de/guides/scripting/several-apps/),
[button events](https://ang.blueforcer.de/guides/scripting/time-buttons-sensors/) and
[TC002 controls](https://ang.blueforcer.de/guides/device-controls/).

## Requirements

- TC002 running official AWTRIX NG beta 1.1.6 with its on-demand API and URL pictures.
- Home Assistant's MQTT and Sonos integrations; both clock and HA use the same broker.
- One Sonos `media_player` entity available in Home Assistant.
- Firmware input topics `<clock-prefix>/state/buttons/knob` and
  `<clock-prefix>/event/knob` enabled for rotary control.
- MQTT credentials belong in the device/HA settings, never Berry source or this repository.

## Install Home Assistant

1. [Import the blueprint into Home Assistant](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Flucaamo%2Ftc002-sonos-remote%2Fblob%2Fmain%2Fhome-assistant%2Fsonos_remote.yaml), or import [the blueprint file](home-assistant/sonos_remote.yaml) in **Settings →
   Automations & scenes → Blueprints**. Use the file's GitHub URL or copy it to
   `config/blueprints/automation/lucaamo/sonos_remote.yaml` and reload automations.
2. Create an automation from **AWTRIX NG Sonos Remote**. Choose your Sonos player
   and a unique MQTT root, e.g. `clock_living_room/sonos_remote`.
3. For album covers, disable **Use fallback icon instead of album artwork**
   and set **Home Assistant URL for native album artwork** to an HTTP(S)
   address reachable from the clock. Leave fallback-only enabled if covers
   are not wanted. Enable the automation.
4. Use the exact same entity and root in the Berry app. Each clock/player pair
   needs a separate automation and root. Do not use a root already owned by the
   older add-on: two responders can execute a command twice.

The blueprint uses fixed native actions:
`media_player.media_play_pause`, `media_next_track`, `media_previous_track`,
`volume_set`, `play_media` and `mqtt.publish`. Command services are invoked
without `?return_response`; no REST response request is needed.

## Install Berry

In the clock web UI's **Scripts** tab, create `sonos_artist_names` and paste
[the artist settings module](apps/sonos_artist_names.ax). Create `sonos_playlists`
and paste [the playlist settings module](apps/sonos_playlists.ax). Save both
modules before creating `sonos_remote` with [the complete app](apps/sonos_remote.ax).
All three compiler results must report `error: null`. Sonos Remote appears in
**In the device menu**, not the ordinary rotation.

HTTP installation:

```sh
curl -fsS -X PUT "http://AWTRIX_IP/api/v1/apps/script/sonos_artist_names" \
  -H 'Content-Type: text/plain' --data-binary @apps/sonos_artist_names.ax
curl -fsS -X PUT "http://AWTRIX_IP/api/v1/apps/script/sonos_playlists" \
  -H 'Content-Type: text/plain' --data-binary @apps/sonos_playlists.ax
curl -fsS -X PUT "http://AWTRIX_IP/api/v1/apps/script/sonos_remote" \
  -H 'Content-Type: text/plain' --data-binary @apps/sonos_remote.ax
```

Configure the app using its gear on **Apps**:

| Setting | Meaning |
| --- | --- |
| MQTT topic root | Match the blueprint's root; configurable independently per clock |
| AWTRIX MQTT topic prefix | Copy System → MQTT → Topic prefix; used for knob input and backend-loss exit |
| Sonos player entity | Exactly the entity selected in the blueprint |
| Volume step (%) | 1–25 percentage points per button press |
| Playlist picker hold (ms) | Knob hold threshold to open/cancel the picker; does not change firmware select/menu timing |
| Playlist picker timeout (ms) | Picker closes without playing if no choice is made |
| Fallback icon name | Optional local asset shown when artwork is missing or invalid; empty uses the built-in meter |
| Interface accent colour | Colour for playlist arrows and the built-in fallback meter |

Configure **Playlist 1–10** together in **Apps → Modules → Sonos Playlists →
settings**. Each field is `Name|content id|content type`, empty by default.
Empty or malformed entries are skipped; the picker follows numeric slot order
and wraps between the last configured entry and the first. The module uses ten
config fields and the app eight. The official TC002 beta 1.1.5 was also checked
with a disposable module declaring 30 fields: all were accepted without warnings.
The current `@config` UI has no grouping/column option, so three fields per
playlist would occupy three separate rows. A horizontal editor requires an
AWTRIX web UI extension. No firmware change is needed for the current format.

Playlist examples (enter literal `|` separators):

```text
Radio|SQ:10|favorite_item_id
Relax|spotify:playlist:PLAYLIST_ID|playlist
```

Names are personal settings; no Spotify login or author's playlist ids are
needed by this app. Check the content id/type with HA's action tester first.
Saving settings ends an active on-demand session; start it again from the menu.
### Upgrade from 3.0.1 or 3.1.0

Back up the old app source and configuration first. **Before replacing the
app**, install `sonos_playlists` and copy the four old `playlist1`–`playlist4`
values into its corresponding fields. Leave slots 5–10 empty until needed.
Then update `sonos_remote`. The playlist keys now belong to the module; the
eight other app keys retain their names. Verify the four entries and your
player/root/volume settings after saving. Upgrading the artist module to 2.0.0
also requires the separate rule migration described below.

Upgrading from 3.0.1 also preserves the `long_ms` value but changes its function
from app exit to playlist selection, as introduced in 3.1.0.

## Display and artist rules

Artist and title are white, centred in the 35 columns to the right of the
16×16 artwork/icon area. Artist is uppercase. Long titles scroll. For long
artists, an explicitly configured short name remains centred after one full
pass; unconfigured names and groups keep scrolling in full.

In **Modules → Sonos Artist Names → settings**, **Global artist rules** is one
optional list for every playlist, favourite and music source. It is empty on a
new installation: full names keep scrolling, without guessing which word is a
first name, surname or band name. Add only the abbreviations you want, such as:

```text
Vasco Rossi|Vasco;Natalie Imbruglia|Natalie;Backstreet Boys|*
```

`*` means continuous full-name scrolling. Matching trims spaces and ignores
ASCII case; last duplicate wins. **Global rule overrides** is an optional
second field whose entries have priority over the main list; `Backstreet Boys|*`
there also cancels an abbreviation from the main list. A short name that does
not fit never replaces the full name. Rules apply to the artist, independently
of the selected playlist. They are user-curated settings, not a live Spotify
artist catalogue. The main list accepts up to 16,384 characters and overrides
up to 2,048 on the tested TC002 beta.

### Upgrade the artist module from 1.x to 2.0.0

Back up the module source and settings **before replacing it**. Copy the four
old rule fields (`relax`, `estate`, `hits`, `nineties`, or Artist rules 1–4)
into **Global artist rules**, in that order, separating the lists with `;`.
Copy the old `aliases` / override field into **Global rule overrides**. Install
the new module, save both fields, and start Sonos Remote again. Empty fields
intentionally mean no abbreviations. Old keys are not read by version 2.0.0;
upgrading the source alone does not migrate saved rules automatically.

Every volume press restarts a two-second `SONOS` / `xx%` overlay. A three-second
settling window suppresses stale HA volume reports, including reports arriving
after a matching echo. MQTT loss ends the session after 65 seconds without
state reception; native select-hold remains available throughout.

## Optional artwork

On official TC002 beta 1.1.6, the blueprint publishes the player's
`entity_picture` URL on `<root>/state/cover`. Relative paths are resolved using
the configured Home Assistant address. Sonos Remote passes that URL to native
`icon()`; the firmware downloads, caches and resizes JPEG/PNG to 16×16.
No external converter, long-lived Home Assistant token or per-pixel drawing
is needed. A missing cover clears the previous image and shows the fallback.

URL payload: `{"width":16,"height":16,"image":"https://example.org/album.jpg"}`.
URLs must be at most 2048 characters, have no whitespace, and be reachable
from the clock. Self-signed HTTPS is unsupported. Keep your MQTT network
private: proxy URLs can contain temporary artwork access tokens.

The earlier static 16×16 GIF Base64 payload (at most 4096 characters) and
256-element RGB888 `pixels` payload remain compatible. For an external
publisher, leave the HA artwork URL empty and turn off fallback-only.
Inline JPEG Base64 is still rejected because it has different size limits.
The built-in animated equalizer works without image dependencies; the local
LaMetric Music Meter `22046` asset is not included, and no third-party artwork
is redistributed.

## Development

See [architecture and extension guide](docs/ARCHITECTURE.md) for the MQTT
protocol, input ownership, validation and concurrency rules.

```sh
python3 -m pip install -r requirements-dev.txt
python3 -m unittest discover -s tests -v
```

The actual Berry runtime and isolated fresh-config test instructions are in
[docs/TESTING.md](docs/TESTING.md). Automated input-handler checks do not replace
physical knob/button testing. Back up your scripts and settings before replacing
a working v2 controller; no firmware flashing is required.

## License

[PolyForm Noncommercial 1.0.0](LICENSE.md); see [NOTICE.md](NOTICE.md) for the
required AWTRIX NG notice and provenance. AWTRIX, Ulanzi, Sonos, Home Assistant,
Spotify and LaMetric are trademarks/names of their respective owners. This
unofficial repository does not imply their endorsement.

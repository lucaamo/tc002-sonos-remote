# AWTRIX Hub distribution

Sonos Remote 3.3.1 is published on the AWTRIX Hub as an on-demand Berry app
for a TC002 running official AWTRIX NG beta 1.1.6.

## Install from the Hub

1. Open [Sonos Remote for TC002](https://awtrix.de/flow/aEY8TgwXGejR) and sign in.
2. Choose **Send to AWTRIX**, enter the clock's local address, and use
   `sonos_remote` as the script name. Reuse that name when updating.
3. Choose **Install with dependencies** when the Hub lists the two missing modules.
   In the clock's own script editor, the equivalent button is **Install all**.
4. Set up Home Assistant and the app settings as described below.

Hub-page installation was tested with both modules initially absent. Saving
a script through the clock's own editor requires a Hub connection key in that
browser, under **System → AWTRIX Hub**. No key was saved as part of this test.

## Files on the clock

| Install name | Hub page | Role |
| --- | --- | --- |
| `sonos_remote` | [Sonos Remote](https://awtrix.de/flow/aEY8TgwXGejR) | Display and physical controls |
| `sonos_playlists` | [Sonos Playlists](https://awtrix.de/flow/n3qg0xvkXEOz) | Ten configurable playlist/favourite slots |
| `sonos_artist_names` | [Sonos Artist Names](https://awtrix.de/flow/baBjYpGc2gcK) | Optional global artist abbreviations |

The main app declares both modules with their published, verified Hub IDs:

```berry
# @requires sonos_artist_names baBjYpGc2gcK
# @requires sonos_playlists n3qg0xvkXEOz
```

The dependency installer saves each module under its exact import name.
For manual installation, the complete files are in `apps/`; install both
modules before the main app. A dependency declaration without a Hub ID would
require installing the missing file manually.

No sound or icon pack is required. A new installation uses the built-in
animated meter when no album cover is available. The optional icon field lets
the user select an icon already installed on their own clock.

## Home Assistant setup

Installing the clock app does not install or configure Home Assistant.

1. [Import the Sonos Remote blueprint into Home Assistant](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Flucaamo%2Ftc002-sonos-remote%2Fblob%2Fmain%2Fhome-assistant%2Fsonos_remote.yaml).
2. Create one automation, selecting a Sonos media player and a unique MQTT root.
3. Set the same player and root in the app settings; copy the clock's own MQTT
   prefix from System → MQTT.
4. For native 16×16 artwork, set an address for Home Assistant that the clock can
   reach and disable fallback-only artwork in the blueprint automation.
5. Configure playlist entries in the Sonos Playlists module. Artist rules are
   optional: leaving them empty keeps complete names scrolling.

Both Home Assistant and the clock must use the same MQTT broker. No old bridge,
TC002 add-on, firmware patch or Home Assistant access token on the clock is
required. A Hub download cannot choose another user's speaker, playlists or
MQTT settings for them.

## Release contents

The modules were published first, their real flow IDs were added to the main
app, and installation from the main Hub page with both modules absent was
verified on official beta 1.1.6. All three downloads matched the repository
code after removing the Hub's generated origin header and normalizing the
trailing newline. New module defaults were empty; existing user settings
were restored and checked. See the [test record](TESTING.md).

Only the current official-framework files above belong in the Hub upload.
Historical compatibility scripts, the old firmware patch and native decoder
proposal are excluded. Images used for the Hub preview contain example data
and original graphics; no album artwork, credentials or private configuration
is uploaded.

License: [PolyForm Noncommercial 1.0.0](../LICENSE.md). Required notice:
Copyright © Stephan Mühl (Blueforcer) https://github.com/Blueforcer/awtrix-ng.

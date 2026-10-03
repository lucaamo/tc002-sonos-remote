# AWTRIX Hub distribution

Sonos Remote 3.3.1 is an on-demand Berry app for a TC002 running official
AWTRIX NG beta 1.1.6. Hub publication is being prepared; until its flow links
are available, use the manual installation steps in the repository README.

## Files on the clock

| Install name | File | Role |
| --- | --- | --- |
| `sonos_remote` | `apps/sonos_remote.ax` | Display and physical controls |
| `sonos_playlists` | `apps/sonos_playlists.ax` | Ten configurable playlist/favourite slots |
| `sonos_artist_names` | `apps/sonos_artist_names.ax` | Optional global artist abbreviations |

The main app declares both modules with `@requires`. Each module must be
installed under its exact import name. After the module flows are published,
their verified Hub IDs can be added to those declarations to enable the
Hub's **Install all** dependency download. A declaration without a Hub ID
identifies a missing module but requires installing it manually.

No sound or icon pack is required. A new installation uses the built-in
animated meter when no album cover is available. The optional icon field lets
the user select an icon already installed on their own clock.

## Home Assistant setup

Installing the clock app does not install or configure Home Assistant.

1. Import the [Sonos Remote blueprint](../home-assistant/sonos_remote.yaml).
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

## Publishing order

Publish Sonos Playlists and Sonos Artist Names as AWTRIX NG Script module
flows first. Record their real flow IDs, add them to the main app's `@requires`
header, and verify a fresh installation before publishing the main app.
Include a clear Home Assistant requirement, a blueprint import link, the
tested firmware version, physical controls and the source repository in the
main flow description.

Only the current official-framework files above belong in the Hub upload.
Historical compatibility scripts, the old firmware patch and native decoder
proposal are excluded. Images used for the Hub preview contain example data
and original graphics; no album artwork, credentials or private configuration
is uploaded.

License: [PolyForm Noncommercial 1.0.0](../LICENSE.md). Required notice:
Copyright © Stephan Mühl (Blueforcer) https://github.com/Blueforcer/awtrix-ng.

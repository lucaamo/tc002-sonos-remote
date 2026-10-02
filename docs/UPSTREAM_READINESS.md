# Official-framework contribution readiness

Version 3.0 supplies a reusable on-demand Berry app and a standalone Home
Assistant blueprint. All entity choices, clock prefixes, playlist entries and
artist aliases are settings. Source defaults contain no author's devices,
credentials, playlist ids or private backups.

## Completed implementation work

1. **Official framework:** `@ondemand` owns entry, exclusive display and exit.
   Three native buttons use `on_button_event`. There are no manual rotation
   pause/resume calls and no hidden global input subscriber.
2. **Home Assistant without the TC002 add-on:** one blueprint selects a Sonos
   entity and unique MQTT root, validates commands, invokes fixed services and
   publishes retained metadata. Album conversion remains optional and separate.
3. **Independent configuration on the available TC002:** temporary new app and
   module identities, empty settings, a different Sonos player and unique MQTT
   root have been tested with the standalone blueprint. Temporary scripts and
   automation are removed afterward. No factory reset was performed and no
   second physical TC002 was available.

The full [test record](TESTING.md) distinguishes code execution, actual HA
service calls, display ownership and remaining physical acceptance.

## Precise upstream API boundary

The official beta 1.1.5 docs expose `@ondemand` and local top-button events.
They explicitly do not route the TC002 knob into Berry hooks. This adapter
therefore retains MQTT for **active-session knob input only**, and sets
`blockNavigation` to suppress the stock knob overlay while controlling Sonos.
Native select-hold still exits. Inactive on-demand scripts are unloaded.

Native entry is firmware menu → Scripts → Sonos Remote, from any carousel
page, or the web UI's Start action. The previous direct global knob hold is
not available through the official API and is not promised in v3.0.

A generic native rotary hook and configurable global app shortcut would remove
this remaining MQTT input dependency. This is a concrete design question for
Blueforcer, not a reason to introduce another Sonos-specific firmware patch.
The old MQTT controller and pinned patch remain historical compatibility files.

## Maintainer review draft (not sent)

> Sonos Remote now uses the documented @ondemand lifecycle and native top-button
> events. We supply a standalone HA blueprint; player, MQTT roots, playlists and
> artist aliases are configuration. A fresh namespace with another Sonos player
> passes runtime, metadata, frame and carousel-recovery tests on beta 1.1.5.
> The TC002 knob still requires active-session MQTT because it is not exposed
> to scripts locally. Would a generic rotary hook and optional configurable
> global shortcut fit your framework? We can adapt the example and test it.

The maintainer decides catalog inclusion or official bundling. No new reply,
Discord message or upstream PR is sent by these implementation steps.

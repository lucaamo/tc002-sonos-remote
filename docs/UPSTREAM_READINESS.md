# Official-framework contribution readiness

Version 3.2.2 supplies a reusable on-demand Berry app and a standalone Home
Assistant blueprint. All entity choices, clock prefixes, playlist entries and
artist aliases are settings. Source defaults contain no author's devices,
credentials, playlist ids or private backups.
Ten playlist slots are collected in the Sonos Playlists module, within the
firmware's config limits; the clock firmware and HA protocol are unchanged.

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
therefore retains MQTT for **active-session knob input and app-requested exit**, and sets
`blockNavigation` to suppress the stock knob overlay while controlling Sonos.
Native select-hold still exits without the broker. Inactive on-demand scripts
are unloaded. During physical testing, Berry `rotation.next()` reopened the
on-demand app on beta 1.1.5; native HTTP/MQTT next unloaded it correctly. The
app now uses the non-retained native MQTT command and tests its actual path.
In 3.1.0 the knob hold opens/cancels playlist selection; top-select hold is
the sole physical exit gesture. The MQTT exit path remains for backend loss.

Native entry is firmware menu → Scripts → Sonos Remote, from any carousel
page, or the web UI's Start action. The previous direct global knob hold is
not available through the official API and is not promised in v3.0.

A generic native rotary hook, configurable global app shortcut and explicit
local script-exit API would remove these remaining MQTT dependencies. These are concrete design questions for
Blueforcer, not a reason to introduce another Sonos-specific firmware patch.
The old MQTT controller and pinned patch remain historical compatibility files.

## Maintainer review draft (not sent)

> Sonos Remote now uses the documented @ondemand lifecycle and native top-button
> events. We supply a standalone HA blueprint; player, MQTT roots, playlists and
> artist aliases are configuration. A fresh namespace with another Sonos player
> passes runtime, metadata, frame and carousel-recovery tests on beta 1.1.5.
> Physical playlist/playback/volume controls pass. The TC002 knob still requires
> active-session MQTT because it is not exposed to scripts locally. We also
> reproduced rotation.next() reopening an on-demand app; native MQTT next exits
> correctly. Would a generic rotary hook, local exit API and optional global
> shortcut fit your framework? We can provide the reproduction and test changes.

The maintainer decides catalog inclusion or official bundling. No new reply,
Discord message or upstream PR is sent by these implementation steps.

## Native artwork candidate (2026-10-02)

The [native conversion candidate](../native-artwork/README.md) supplies real
host-executed C++ JPEG/PNG decoding, 10×10/16×16 resampling, byte/dimension/
allocation bounds, and cache/session generation handling. It is generic and
contains no Home Assistant or Sonos installation identifiers. It is a source
building block, **not an implemented firmware image API**.

Integration into official beta is pending: its 1.1.5 source commit cannot be
resolved in the accessible public repository, which lacks the matching Linux
and TC002 adapters. The native HTTP worker, Berry bindings and device tests
must be completed against those sources. No device firmware, Berry app or HA
automation was changed for this candidate. A maintainer message draft is in
that directory; it has not been sent.

# Reference firmware patch

`tc002-v1.1.2-tc002.1-global-sonos-shortcut.patch` is the exact native-input
proof of concept tested with the TC002 port at:

```text
base tag:    v1.1.2-tc002.1
base commit: b1bd3fbc905a85790dd6771c972e4776338f4a95
tested head: 55a81ffd810adab88b06beb8c95ec96fddb6f826
```

It adds:

- a global select-button hold that activates `sonos_remote`;
- lookup of the Berry `long_ms` value from the script store;
- first-refusal routing for the physical rocker;
- host-side tests for hidden-carousel, entry, exit, rotary, and rocker behaviour.

## Compatibility warning

This patch changes TC002 native code and is tied to the exact base above. It
already conflicts with later TC002 port work such as `v1.1.2-tc002.3`. Do not
apply it blindly to current `main`, do not distribute a binary made from it as
an official AWTRIX NG release, and do not flash a device without a separately
verified recovery path.

The preferred upstream solution is a generic configurable shortcut or an input
event API that any Berry app can register, rather than a Sonos-specific constant
in the firmware. That proposal is being discussed in
[AWTRIX NG discussion #66](https://github.com/Blueforcer/awtrix-ng/discussions/66).

For historical reproduction only:

```sh
git checkout b1bd3fbc905a85790dd6771c972e4776338f4a95
git apply /path/to/tc002-v1.1.2-tc002.1-global-sonos-shortcut.patch
```

Review every hunk and port it deliberately if the input architecture has
changed. The repository intentionally contains no toolchain, vendor library,
filesystem image, or firmware binary.

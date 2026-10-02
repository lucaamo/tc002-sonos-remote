# Native image conversion candidate for AWTRIX NG

**Source-only, host-tested building block. Not installed firmware and not a
function available in official TC002 beta 1.1.5.** The current Sonos Remote app
and its Home Assistant blueprint are unchanged. No device binary is supplied.

The intended result is a generic native image API that any Berry app can use:
Home Assistant supplies the image URL; AWTRIX downloads, decodes and resamples
the image on the clock. There is no Home Assistant converter, long-lived HA
token on the clock, image-processing daemon, or persistent cover file.

## Implemented and executable

- `Artwork.cpp`: JPEG, progressive JPEG and PNG decoding with a pinned MIT
  `stb_image` decoder. Center crop to the requested aspect ratio and weighted
  area resampling avoid stretching and aliasing. Transparency is composited
  over black. Output is row-major RGB888, 100 pixels at 10×10 or 256 at 16×16.
- `EncodedBuffer`: reject an HTTP body at the byte limit **while receiving it**.
- `Session`: one RAM image cache, URL/size change detection, opaque generation
  tickets, old-image clearing, retry after failure, and rejection of stale,
  duplicate, wrong-size or unloaded-session results.
- A C++ driver and Python tests run the actual native decoder and lifecycle
  coordinator; images are generated for tests, not distributed album artwork.

Limits in this candidate: 1 MiB encoded body, 1,048,576 source pixels, source
edge at most 2048, target edge at most 32 and 6 MiB of decoder allocations.
Allocation headers, the bounded encoded buffer and tiny output frame add to
that budget. These limits require native-worker admission control before a
job on the TC002; they are **not an ESP32 memory policy**. The target clock's
memory and latency measurements are still pending.

`decode()` runs in a worker; `Session` is used only by the main thread.
Its completion ticket and image must be posted through the native result queue.
The worker must never call Berry, draw to the display, or dereference a script
instance. The renderer reads only the completed frame already in memory.

## Not implemented against the unavailable beta source

The authenticated GitHub account used for this work could read public `main`
at `6d6cc64aa6739724d8501199de70c6692cbb2c6c`, but could not resolve the installed
beta 1.1.5 commit `6e19de7d216f`. The public tree has no `src/platform/tc002/`
or `src/platform/linux/` adapter matching that beta. The newer developer docs
describe those directories, but do not supply their contents.

Therefore this directory deliberately contains **no purported beta patch**.
The following work needs its matching source tree and maintainer agreement:

1. Attach a single coalescing image worker to AWTRIX's native HTTP/TLS transport.
   Check available memory, stream into `EncodedBuffer`, apply timeout and body
   bounds, validate final URL scheme on every redirect, and verify certificates.
   Same URL/size requests reuse the cached image; failures retry with backoff,
   not every display frame. Give commands and the renderer priority.
2. Register the Berry image load/draw/clear bindings and report the capability.
   An app on unsupported firmware must retain its existing fallback. The names
   below are a **proposal**, not existing APIs.
3. Invalidate the session on a new image, app unload, disable, replacement and
   teardown. A worker may finish later, but its generation cannot become visible.
4. Adapt the Sonos metadata blueprint to publish an absolute, accessible
   `artwork_url`. Resolve HA's relative image proxy against a configurable HA
   URL. Do not print signed URLs, put them into persistent Berry config, or send
   a permanent HA bearer token to AWTRIX. Clear the URL when metadata is missing.
5. Adapt Sonos Remote to load only on URL/size change and draw the resident
   result. Preserve the existing controls, artist rules and playlist picker.
6. Build from the exact beta source and test on ARM: real album, paused album,
   rapid skips, no artwork, oversized response, TLS/HTTP failures, reboot,
   unload, RAM, FPS and input latency. Only then install a reviewed candidate.

Optional proposed API:

```text
image.load(url, {width: 16, height: 16}, callback) -> request ticket
image.draw(handle, x, y) -> bool
image.clear(handle)
```

Native handles should retain a small RGB frame, not an entire JPEG or Berry
list of 256 objects. No Sonos entity, player name, MQTT root, playlist or artist
mapping belongs in the firmware. EXIF orientation and color-profile handling
are not yet included; this prototype assumes normal unrotated cover artwork.

## Tests

From the repository root, with a C++17 compiler:

```sh
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -p test_native_artwork.py -v
```

`CXX` selects the compiler; `CXXFLAGS` can enable sanitizers. CI runs native
tests with AddressSanitizer and UndefinedBehaviorSanitizer on Linux. A missing
compiler fails the tests; it is not silently skipped.

## Maintainer message draft — not sent

> Would a generic native image API fit AWTRIX NG on TC002? We prepared a small
> C++ JPEG/PNG decoder and bounded resampler, plus a RAM cache/session coordinator
> with generation checks for stale downloads and app unloads. Actual native
> tests cover 10×10/16×16 output, progressive JPEG, alpha, crop, malformed inputs,
> byte/dimension/memory bounds and out-of-order results under ASan/UBSan.
> Home Assistant would send only the artwork URL; the clock would do the image
> processing. The candidate is source-only: we have not patched or replaced your
> beta. Could you share the matching 1.1.5 source or indicate the preferred
> native worker/Berry API so we can finish the adapter and test it on hardware?

Code: <https://github.com/lucaamo/tc002-sonos-remote/tree/main/native-artwork>

Required Notice: Copyright © Stephan Mühl (Blueforcer) https://github.com/Blueforcer/awtrix-ng

`vendor/stb_image.h` remains MIT, option A of its upstream dual license; its
license, pinned commit and SHA-256 are in `vendor/`. The surrounding candidate
is distributed under the repository's PolyForm Noncommercial license.

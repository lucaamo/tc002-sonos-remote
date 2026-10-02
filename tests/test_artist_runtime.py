from __future__ import annotations

import json
import os
import re
import time
import unittest
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build_runtime_probe() -> tuple[str, str, str]:
    app = (ROOT / "apps/sonos_remote.ax").read_text(encoding="utf-8")
    module = (ROOT / "apps/sonos_artist_names.ax").read_text(encoding="utf-8")
    module = module.replace("sonos_artist_names", "sonos_artist_test_names")
    fixtures = {
        "overrides": " Vasco Rossi | Vasco ; Natalie Imbruglia | Natalie ;Backstreet Boys|*;"
                   "invalid;Empty Artist|   ;Duplicate Artist|First;Duplicate Artist|Last",
        "rules": "Global Artist|Global;Vasco Rossi|Other;Backstreet Boys|Wrong;"
                 "Duplicate Artist|Original;" + ";".join(
                     f"Catalogue Artist {n}|C{n}" for n in range(400)),
    }
    for key, value in fixtures.items():
        module, count = re.subn(
            rf'(# @config {key} text "[^"]+" default=)"[^"]*"',
            lambda match: match[1] + '"' + value + '"', module,
        )
        if count != 1:
            raise ValueError(f"Missing or duplicated module setting: {key}")
    playlists = (ROOT / "apps/sonos_playlists.ax").read_text(encoding="utf-8").replace(
        "sonos_playlists", "sonos_playlist_test_slots")
    for slot in range(1, 11):
        playlists, count = re.subn(
            rf'(# @config playlist{slot} text "[^"]+" default=)"[^"]*"',
            lambda match: match[1] + f'"List {slot}|spotify:playlist:EXAMPLE_{slot}|playlist"', playlists,
        )
        if count != 1:
            raise ValueError(f"Missing or duplicated playlist slot: {slot}")
    klass = app[app.index("class SonosRemote"):app.rindex("return SonosRemote()")].strip()
    configs = "\n".join(line for line in app.splitlines() if line.startswith("# @config "))
    harness = (ROOT / "tests/artist_runtime.ax.in").read_text(encoding="utf-8")
    harness = harness.replace("__CONFIG__", configs).replace(
        "__CLASS__", "\n".join("  " + line for line in klass.splitlines())
    )
    return module, playlists, harness


@unittest.skipUnless(os.environ.get("AWTRIX_TEST_URL"), "set AWTRIX_TEST_URL for Berry runtime checks")
class ArtistRuntimeTests(unittest.TestCase):
    def test_actual_berry_artist_state_and_module_parser(self) -> None:
        base = os.environ["AWTRIX_TEST_URL"].rstrip("/") + "/api/v1/"

        def request(method: str, path: str, source: str | None = None):
            req = urllib.request.Request(
                base + path, method=method,
                data=source.encode("utf-8") if source is not None else None,
                headers={"Content-Type": "text/plain"},
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                return json.load(response)

        module, playlists, harness = build_runtime_probe()
        installed = []
        names = {"sonos_artist_test_names", "sonos_playlist_test_slots", "sonos_artist_regression"}
        if names & {a["name"] for a in request("GET", "apps")}:
            self.fail("Runtime test names already exist; refusing to replace them")
        try:
            for name, source in (("sonos_artist_test_names", module), ("sonos_playlist_test_slots", playlists), ("sonos_artist_regression", harness)):
                installed.append(name)
                result = request("PUT", "apps/script/" + name, source)
                self.assertIsNone(result.get("error"), result)
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                apps = {app["name"]: app for app in request("GET", "apps")}
                self.assertIsNone(apps["sonos_artist_regression"].get("error"))
                checks = [item for item in request("GET", "scripts/shared")
                          if item.get("owner") == "sonos_artist_regression"]
                counts = [int(match[1]) for item in checks
                          if isinstance(item.get("value"), str)
                          and (match := re.fullmatch(r"(\d+) runtime checks passed", item["value"]))]
                if counts:
                    self.assertGreaterEqual(max(counts), 89, "runtime coverage unexpectedly decreased")
                    print(f"Berry runtime: {max(counts)} checks passed")
                    break
                time.sleep(0.1)
            else:
                self.fail("Berry runtime probe did not report successful checks")
        finally:
            for name in reversed(installed):
                request("DELETE", "apps/" + name)


if __name__ == "__main__":
    unittest.main()

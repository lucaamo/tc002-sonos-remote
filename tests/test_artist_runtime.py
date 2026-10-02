from __future__ import annotations

import json
import os
import re
import time
import unittest
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build_runtime_probe() -> tuple[str, str]:
    app = (ROOT / "apps/sonos_remote.ax").read_text(encoding="utf-8")
    module = (ROOT / "apps/sonos_artist_names.ax").read_text(encoding="utf-8")
    module = module.replace("sonos_artist_names", "sonos_artist_test_names")
    fixtures = {
        "aliases": " Vasco Rossi | Vasco ; Natalie Imbruglia | Natalie ;Backstreet Boys|*;"
                   "invalid;Empty Artist|   ;Duplicate Artist|First;Duplicate Artist|Last",
        "relax": "Playlist Artist|Relax;Vasco Rossi|Other",
        "estate": "Playlist Artist|Estate",
        "hits": "Hits Artist|Hits",
        "nineties": "Playlist Artist|Nineties",
    }
    for key, value in fixtures.items():
        module, count = re.subn(
            rf'(# @config {key} text "[^"]+" default=)"[^"]*"',
            lambda match: match[1] + '"' + value + '"', module,
        )
        if count != 1:
            raise ValueError(f"Missing or duplicated module setting: {key}")
    klass = app[app.index("class SonosRemote"):app.rindex("return SonosRemote()")].strip()
    configs = "\n".join(line for line in app.splitlines() if line.startswith("# @config "))
    harness = (ROOT / "tests/artist_runtime.ax.in").read_text(encoding="utf-8")
    harness = harness.replace("__CONFIG__", configs).replace(
        "__CLASS__", "\n".join("  " + line for line in klass.splitlines())
    )
    return module, harness


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

        module, harness = build_runtime_probe()
        installed = []
        try:
            for name, source in (("sonos_artist_test_names", module), ("sonos_artist_regression", harness)):
                installed.append(name)
                result = request("PUT", "apps/script/" + name, source)
                self.assertIsNone(result.get("error"), result)
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline:
                apps = {app["name"]: app for app in request("GET", "apps")}
                self.assertIsNone(apps["sonos_artist_regression"].get("error"))
                checks = [item for item in request("GET", "scripts/shared")
                          if item.get("owner") == "sonos_artist_regression"]
                if any(item.get("value") == "54 runtime checks passed" for item in checks):
                    break
                time.sleep(0.1)
            else:
                self.fail("Berry runtime probe did not report successful checks")
        finally:
            for name in reversed(installed):
                request("DELETE", "apps/" + name)


if __name__ == "__main__":
    unittest.main()

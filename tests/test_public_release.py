from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps" / "sonos_remote.ax").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
LICENSE = (ROOT / "LICENSE.md").read_text(encoding="utf-8")
PATCH = (ROOT / "patches" / "tc002-v1.1.2-tc002.1-global-sonos-shortcut.patch").read_text(
    encoding="utf-8"
)


class PublicReleaseTests(unittest.TestCase):
    def test_berry_contract(self) -> None:
        self.assertIn("# @version 2.1", APP)
        self.assertIn('default="tc002/sonos_remote/v2"', APP)
        self.assertIn('"player_entity_id":self.player', APP)
        self.assertIn('"action":"play_media"', APP)
        self.assertTrue(APP.rstrip().endswith("return SonosRemote()"))

    def test_exclusive_input_mapping(self) -> None:
        self.assertIn("rotation.pause()", APP)
        self.assertIn("rotation.resume()", APP)
        self.assertIn('btn == "right" self.send("next")', APP)
        self.assertIn('btn == "left" self.send("previous")', APP)
        self.assertIn('btn != "rocker_left" && btn != "rocker_right"', APP)
        self.assertIn('self.send("play_pause")', APP)

    def test_missing_optional_icon_has_fallback(self) -> None:
        self.assertIn('if !icon("sonos_music_meter", 0, 6)', APP)
        self.assertIn("rect_fill", APP)
        self.assertIn("not included", README)

    def test_license_notice_is_preserved(self) -> None:
        notice = (
            "Required Notice: Copyright © Stephan Mühl (Blueforcer) "
            "https://github.com/Blueforcer/awtrix-ng"
        )
        self.assertIn(notice, LICENSE)
        self.assertIn(notice, (ROOT / "NOTICE.md").read_text(encoding="utf-8"))

    def test_reference_patch_is_pinned(self) -> None:
        patch_readme = (ROOT / "patches" / "README.md").read_text(encoding="utf-8")
        self.assertIn("b1bd3fbc905a85790dd6771c972e4776338f4a95", patch_readme)
        self.assertIn("55a81ffd810adab88b06beb8c95ec96fddb6f826", patch_readme)
        self.assertIn("setRockerHook", PATCH)
        self.assertIn('kSonosRemoteApp = "sonos_remote"', PATCH)

    def test_no_known_private_identifiers_or_credentials(self) -> None:
        public_text = "\n".join(
            path.read_text(encoding="utf-8", errors="replace")
            for path in ROOT.rglob("*")
            if path.is_file()
            and ".git" not in path.parts
            and "__pycache__" not in path.parts
            and path != Path(__file__).resolve()
        )
        forbidden = (
            r"192\.168\.1\.",
            "ccc4" + "b2779853",
            r"media_player\.sonos_soggiorno",
            "AirPort" + " Home",
            "/Volumes/" + "Backup HA",
            r"mqtt_password\s*[:=]\s*[^\s\"']+",
        )
        for pattern in forbidden:
            with self.subTest(pattern=pattern):
                self.assertIsNone(re.search(pattern, public_text, re.IGNORECASE))

    def test_command_services_do_not_request_responses(self) -> None:
        self.assertNotIn("?return_response", APP)
        self.assertIn("without `?return_response`", README)


if __name__ == "__main__":
    unittest.main()

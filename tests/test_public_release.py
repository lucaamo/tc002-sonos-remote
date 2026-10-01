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
        self.assertIn("# @version 2.5", APP)
        self.assertIn('default="tc002/sonos_remote/v2"', APP)
        self.assertIn('"player_entity_id":self.player', APP)
        self.assertIn('"action":"play_media"', APP)
        self.assertNotIn('"/state/playlists"', APP)
        self.assertEqual(APP.count("# @config "), 12)
        self.assertTrue(APP.rstrip().endswith("return SonosRemote()"))

    def test_exclusive_input_mapping(self) -> None:
        self.assertIn("rotation.pause()", APP)
        self.assertIn("rotation.resume()", APP)
        self.assertIn('"/event/knob"', APP)
        self.assertIn('"/state/buttons/right"', APP)
        self.assertIn('"/state/buttons/left"', APP)
        self.assertIn('self.send("play_pause")', APP)

    def test_playlist_picker_contract(self) -> None:
        for slot in range(1, 5):
            self.assertIn(f'# @config playlist{slot} text "Playlist {slot}"', APP)
            self.assertIn(f'store.get("playlist{slot}")', APP)
        self.assertIn('re.search("^([^|]+)\\\\|([^|]+)\\\\|([^|]+)$", spec)', APP)
        self.assertIn("self.playlist_index = (self.playlist_index + turns) % count", APP)
        self.assertIn('"media_content_id":content_id', APP)
        self.assertIn('"media_content_type":content_type', APP)
        self.assertIn('var heading = "PLAYLIST"', APP)
        self.assertIn("self.picker_until = now_ms() + self.picker_ms", APP)

    def test_missing_optional_icon_has_fallback(self) -> None:
        self.assertIn('if !icon(self.icon_name, 0, 6)', APP)
        self.assertIn("rect_fill", APP)
        self.assertIn("not included", README)

    def test_album_cover_is_drawn_in_ram_with_icon_fallback(self) -> None:
        self.assertIn('"/state/cover"', APP)
        self.assertIn("size(self.cover) == 100", APP)
        self.assertIn("pixel(cover_x, 6 + cover_y", APP)

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

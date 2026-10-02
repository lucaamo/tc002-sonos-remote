from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "apps" / "sonos_remote.ax").read_text(encoding="utf-8")
PLAYLISTS = (ROOT / "apps" / "sonos_playlists.ax").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
LICENSE = (ROOT / "LICENSE.md").read_text(encoding="utf-8")
PATCH = (ROOT / "patches" / "tc002-v1.1.2-tc002.1-global-sonos-shortcut.patch").read_text(
    encoding="utf-8"
)


class PublicReleaseTests(unittest.TestCase):
    def test_berry_contract(self) -> None:
        self.assertIn("# @version 3.2.1", APP)
        self.assertIn('default="tc002/sonos_remote/v2"', APP)
        self.assertIn('"player_entity_id":self.player', APP)
        self.assertIn('"action":"play_media"', APP)
        self.assertNotIn('"/state/playlists"', APP)
        self.assertEqual(APP.count("# @config "), 8)
        self.assertEqual(PLAYLISTS.count("# @config "), 10)
        self.assertIn("import sonos_playlists", APP)
        self.assertTrue(APP.rstrip().endswith("return SonosRemote()"))

    def test_new_install_has_no_personal_configuration(self) -> None:
        self.assertIn('# @config device_root text "AWTRIX MQTT topic prefix" default=""', APP)
        self.assertNotIn('default="tc002-sonos-ng"', APP)
        self.assertIn('if self.device_root != ""', APP)
        module = (ROOT / "apps/sonos_artist_names.ax").read_text(encoding="utf-8")
        defaults = re.findall(r'^# @config \w+ text "[^"]+" default="([^"]*)"', module, re.M)
        self.assertEqual(defaults, [""] * 2)
        self.assertIn('# @config rules text "Global artist rules"', module)
        self.assertIn('# @config overrides text "Global rule overrides"', module)
        for key in ("relax", "estate", "hits", "nineties", "aliases"):
            self.assertNotRegex(module, rf"# @config {key} ")

    def test_exclusive_input_mapping(self) -> None:
        self.assertIn("# @ondemand", APP)
        self.assertNotIn("rotation.pause()", APP)
        self.assertNotIn("rotation.resume()", APP)
        self.assertIn("def on_button_event(btn, event)", APP)
        self.assertIn('"/event/knob"', APP)
        self.assertNotIn('"/state/buttons/+"', APP)
        self.assertNotIn('"/state/buttons/right"', APP)
        self.assertIn('self.send("play_pause")', APP)

    def test_playlist_picker_contract(self) -> None:
        self.assertIn("# @module sonos_playlists", PLAYLISTS)
        self.assertIn("for slot : 1 .. 10", PLAYLISTS)
        self.assertIn('store.get("playlist" + str(slot))', PLAYLISTS)
        defaults = re.findall(r'^# @config playlist\d+ text "[^"]+" default="([^"]*)"', PLAYLISTS, re.M)
        self.assertEqual(defaults, [""] * 10)
        for slot in range(1, 11):
            self.assertIn(f'# @config playlist{slot} text "Playlist {slot}"', PLAYLISTS)
        self.assertIn("for spec : sonos_playlists.entries self.add_playlist(spec) end", APP)
        self.assertIn('re.search("^([^|]+)\\\\|([^|]+)\\\\|([^|]+)$", spec)', APP)
        self.assertIn("self.playlist_index = (self.playlist_index + turns) % count", APP)
        self.assertIn('"media_content_id":content_id', APP)
        self.assertIn('"media_content_type":content_type', APP)
        self.assertIn('var heading = "PLAYLIST"', APP)
        self.assertIn("self.picker_until = now_ms() + self.picker_ms", APP)

    def test_missing_optional_icon_has_fallback(self) -> None:
        self.assertIn('if !icon(self.icon_name, 3, 3)', APP)
        self.assertIn("rect_fill", APP)
        self.assertIn("not included", README)

    def test_album_cover_is_drawn_in_ram_with_icon_fallback(self) -> None:
        self.assertIn('"/state/cover"', APP)
        self.assertIn("size(self.cover) == 256", APP)
        self.assertIn("pixel(cover_x, cover_y", APP)
        self.assertIn("var text_x = 17", APP)

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

# Historical MQTT entry adapter

`sonos_remote_mqtt_v2.ax` preserves the neutral v2.8 source before adaptation
to the official on-demand framework. It uses a hidden global MQTT listener for
knob-hold entry and manual carousel pause/resume. It imports the same artist
settings module and follows the same media MQTT contract.

Use `apps/sonos_remote.ax` for the new official framework. Do not enable both
adapters for one clock/player/root. v2 is historical compatibility material;
its earlier physical prototype tests do not certify every AWTRIX firmware.

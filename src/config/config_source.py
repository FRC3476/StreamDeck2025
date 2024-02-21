import os
from dataclasses import dataclass

import ntcore
from config.config_store import ButtonConfig, ConfigStore


class ConfigSource:
    def update(self, config_store: ConfigStore):
        del config_store
        raise NotImplementedError


class EnvironmentConfigSource(ConfigSource):
    def update(self, config_store: ConfigStore):
        config_store.server_ip = os.environ.get("SD_NT_SERVER_IP", config_store.server_ip)
        config_store.asset_directory = os.environ.get("SD_ASSET_DIRECTORY", config_store.asset_directory)


@dataclass
class ButtonSource:
    key: ntcore.StringSubscriber
    selected: ntcore.BooleanSubscriber
    icon: ntcore.StringSubscriber
    label: ntcore.StringSubscriber


class NTConfigSource(ConfigSource):
    def __init__(self, num_buttons: int):
        self._init_complete = False
        self._num_buttons = num_buttons
        self._button_sources: list[ButtonSource]

    def update(self, config_store: ConfigStore):
        if not self._init_complete:
            deck_table = ntcore.NetworkTableInstance.getDefault().getTable("StreamDeck")
            self._button_sources = []
            for i in range(self._num_buttons):
                table = deck_table.getSubTable(f"Button/{i}")
                self._button_sources.append(
                    ButtonSource(
                        table.getStringTopic("Key").subscribe(ButtonConfig.key),
                        table.getBooleanTopic("Selected").subscribe(False),
                        table.getStringTopic("Icon").subscribe(ButtonConfig.icon),
                        table.getStringTopic("Label").subscribe(ButtonConfig.label),
                    )
                )
            self._init_complete = True

        config_store.remote_connected = ntcore.NetworkTableInstance.getDefault().isConnected()
        config_store.buttons = [
            ButtonConfig(button.key.get(), button.selected.get(), button.icon.get(), button.label.get())
            for button in self._button_sources
        ]

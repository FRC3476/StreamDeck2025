import os
from dataclasses import dataclass
import constants
from nt_instances import nt_instance
if constants.DO_SIM:
    from nt_instances import nt_instance_sim
import ntcore
from config.config_store import ButtonConfig, ConfigStore

class ConfigSource:
    def update(self, config_store: ConfigStore):
        del config_store
        raise NotImplementedError


class EnvironmentConfigSource(ConfigSource):
    def update(self, config_store: ConfigStore):
        config_store.server_ip = os.environ.get("SD_NT_SERVER_IP", config_store.server_ip)
        if constants.DO_SIM:
            config_store.server_ip_sim = os.environ.get("SD_NT_SERVER_IP_SIM", config_store.server_ip_sim)

@dataclass
class ButtonSource:
    key: ntcore.StringSubscriber
    selected: ntcore.BooleanSubscriber
    active_background: ntcore.StringSubscriber
    inactive_background: ntcore.StringSubscriber
    active_foreground: ntcore.StringSubscriber
    inactive_foreground: ntcore.StringSubscriber
    active_text: ntcore.StringSubscriber
    inactive_text: ntcore.StringSubscriber


class NTConfigSource(ConfigSource):
    def __init__(self, num_buttons: int):
        self._init_complete = False
        self._num_buttons = num_buttons
        self._button_sources: list[ButtonSource] = []
        if constants.DO_SIM:
            self._button_sources_sim: list[ButtonSource] = []

    def update(self, config_store: ConfigStore):
        if not self._init_complete:
            deck_table = nt_instance.getTable("StreamDeck")
            for i in range(self._num_buttons):
                table = deck_table.getSubTable(f"Button/{i}")
                self._button_sources.append(
                    ButtonSource(
                        table.getStringTopic("Key").subscribe(ButtonConfig.key),
                        table.getBooleanTopic("Selected").subscribe(False),
                        table.getStringTopic("ActiveBackground").subscribe(ButtonConfig.active_background),
                        table.getStringTopic("InactiveBackground").subscribe(ButtonConfig.inactive_background),
                        table.getStringTopic("ActiveForeground").subscribe(ButtonConfig.active_foreground),
                        table.getStringTopic("InactiveForeground").subscribe(ButtonConfig.inactive_foreground),
                        table.getStringTopic("ActiveText").subscribe(ButtonConfig.active_text),
                        table.getStringTopic("InactiveText").subscribe(ButtonConfig.inactive_text),
                    )
                )
                if constants.DO_SIM:
                    deck_table_sim = nt_instance_sim.getTable("StreamDeck")
                    table = deck_table_sim.getSubTable(f"Button/{i}")
                    self._button_sources_sim.append(
                        ButtonSource(
                            table.getStringTopic("Key").subscribe(ButtonConfig.key),
                            table.getBooleanTopic("Selected").subscribe(False),
                            table.getStringTopic("ActiveBackground").subscribe(ButtonConfig.active_background),
                            table.getStringTopic("InactiveBackground").subscribe(ButtonConfig.inactive_background),
                            table.getStringTopic("ActiveForeground").subscribe(ButtonConfig.active_foreground),
                            table.getStringTopic("InactiveForeground").subscribe(ButtonConfig.inactive_foreground),
                            table.getStringTopic("ActiveText").subscribe(ButtonConfig.active_text),
                            table.getStringTopic("InactiveText").subscribe(ButtonConfig.inactive_text),
                        )
                )
            self._init_complete = True

        config_store.remote_connected = nt_instance.isConnected()
        config_store.buttons = [
            ButtonConfig(
                button.key.get(),
                button.selected.get(),
                button.active_background.get(),
                button.inactive_background.get(),
                button.active_foreground.get(),
                button.inactive_foreground.get(),
                button.active_text.get(),
                button.inactive_text.get()
                )
            for button in self._button_sources
        ]

        if constants.DO_SIM:
            config_store.remote_connected_sim = nt_instance_sim.isConnected()
            config_store.buttons_sim = [
                ButtonConfig(
                    button.key.get(),
                    button.selected.get(),
                    button.active_background.get(),
                    button.inactive_background.get(),
                    button.active_foreground.get(),
                    button.inactive_foreground.get(),
                    button.active_text.get(),
                    button.inactive_text.get()
                    )
                for button in self._button_sources_sim
            ]
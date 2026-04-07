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
        config_store.asset_directory = os.environ.get("SD_ASSET_DIRECTORY", config_store.asset_directory)

@dataclass
class ButtonSource:
    appearance: ntcore.StringSubscriber
    selected: ntcore.BooleanSubscriber


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
                        table.getStringTopic("Appearance").subscribe(""+"$&$"+""+"$&$"+""+"$&$"+""+"$&$"+""+"$&$"+""+"$&$"+""),
                        table.getBooleanTopic("Selected").subscribe(False),
                    )
                )
                if constants.DO_SIM:
                    deck_table_sim = nt_instance_sim.getTable("StreamDeck")
                    table = deck_table_sim.getSubTable(f"Button/{i}")
                    self._button_sources_sim.append(
                        ButtonSource(
                            table.getStringTopic("Appearance").subscribe(""+"$&$"+""+"$&$"+""+"$&$"+""+"$&$"+""+"$&$"+""+"$&$"+""),
                            table.getBooleanTopic("Selected").subscribe(False),
                        )
                )
            self._init_complete = True

        config_store.remote_connected = nt_instance.isConnected()

        buttons = []
        for button in self._button_sources:
            appearance = button.appearance.get()
            key, active_background, inactive_background, active_foreground, inactive_foreground, active_text, inactive_text = appearance.split("$&$")
            buttons.append(ButtonConfig(key, button.selected.get(), active_background, inactive_background, active_foreground, inactive_foreground, active_text, inactive_text))
        config_store.buttons = buttons

        if constants.DO_SIM:
            config_store.remote_connected_sim = nt_instance_sim.isConnected()

            buttons = []
            for button in self._button_sources_sim:
                appearance = button.appearance.get()
                key, active_background, inactive_background, active_foreground, inactive_foreground, active_text, inactive_text = appearance.split("$&$")
                buttons.append(ButtonConfig(key, button.selected.get(), active_background, inactive_background, active_foreground, inactive_foreground, active_text, inactive_text))
            config_store.buttons_sim = buttons

    def cleanup(self):
        """Close all subscribers to prevent resource leaks"""
        if not self._init_complete:
            return
        
        try:
            # Close all button subscribers
            for button_source in self._button_sources:
                button_source.appearance.close()
                button_source.selected.close()
            
            if constants.DO_SIM:
                # Close all sim button subscribers
                for button_source in self._button_sources_sim:
                    button_source.appearance.close()
                    button_source.selected.close()
        except Exception as e:
            print(f"Error during NTConfigSource cleanup: {e}")
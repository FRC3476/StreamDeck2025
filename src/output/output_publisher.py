import time
from dataclasses import dataclass
from typing import override
import constants
from nt_instances import nt_instance, nt_instance_sim
import ntcore
from config.config_store import ConfigStore


class OutputPublisher:
    def send_connected(self, connected: bool):
        del connected
        raise NotImplementedError

    def send_heartbeat(self):
        raise NotImplementedError

    def send_button_selected(self, index: int, selected: bool):
        del index, selected
        raise NotImplementedError


@dataclass
class ButtonPublisher:
    key: str
    selected: ntcore.BooleanPublisher | None


class NTOutputPublisher(OutputPublisher):
    PRESSED_PUBLISH_OPTIONS = ntcore.PubSubOptions(periodic=0.02, sendAll=True)

    def __init__(self, config_store: ConfigStore, num_buttons: int):
        self._init_complete = False
        self._config = config_store
        self._num_buttons = num_buttons
        self._connected: ntcore.BooleanTopic
        self._heartbeat: ntcore.IntegerTopic
        self._buttons: list[ButtonPublisher]
        self._start_time = self.get_time()
        self._connected_sim: ntcore.BooleanTopic
        self._heartbeat_sim: ntcore.IntegerTopic
        self._buttons_sim: list[ButtonPublisher]
        self._start_time_sim = self.get_time()

    def get_time(self) -> int:
        return time.time_ns() //1_000_000

    def _ensure_init(self):
        if not self._init_complete:
            deck_table = nt_instance.getTable("StreamDeck")
            self._connected = deck_table.getBooleanTopic("Connected").publish()
            self._heartbeat = deck_table.getIntegerTopic("Heartbeat").publish()
            deck_table_sim = nt_instance_sim.getTable("StreamDeck")
            self._connected_sim = deck_table_sim.getBooleanTopic("Connected").publish()
            self._heartbeat_sim = deck_table_sim.getIntegerTopic("Heartbeat").publish()

            self._buttons = []
            for i in range(self._num_buttons):
                key = self._config.buttons[i].key if i < len(self._config.buttons) else ""
                self._buttons.append(
                    ButtonPublisher(
                        key,
                        (
                            nt_instance
                            .getBooleanTopic(key)
                            .publish(NTOutputPublisher.PRESSED_PUBLISH_OPTIONS)
                            if key
                            else None
                        ),
                    )
                )

            self._buttons_sim = []
            for i in range(self._num_buttons):
                key = self._config.buttons[i].key if i < len(self._config.buttons) else ""
                self._buttons_sim.append(
                    ButtonPublisher(
                        key,
                        (
                            nt_instance_sim
                            .getBooleanTopic(key)
                            .publish(NTOutputPublisher.PRESSED_PUBLISH_OPTIONS)
                            if key
                            else None
                        ),
                    )
                )

            self._init_complete = True

        for config, pub in zip(self._config.buttons, self._buttons):
            if config.key and (config.key != pub.key):
                pub.key = config.key
                pub.selected = (
                    nt_instance
                    .getBooleanTopic(pub.key)
                    .publish(NTOutputPublisher.PRESSED_PUBLISH_OPTIONS)
                )
        for config, pub in zip(self._config.buttons_sim, self._buttons_sim):
            if config.key and (config.key != pub.key):
                pub.key = config.key
                pub.selected = (
                    nt_instance_sim
                    .getBooleanTopic(pub.key)
                    .publish(NTOutputPublisher.PRESSED_PUBLISH_OPTIONS)
                )

    @override
    def send_connected(self, connected: bool):
        self._ensure_init()
        self._connected.set(connected)
        self._connected_sim.set(connected)

    @override
    def send_heartbeat(self):
        self._ensure_init()
        self._heartbeat.set(self.get_time() - self._start_time)
        self._heartbeat_sim.set(self.get_time() - self._start_time_sim)

    @override
    def send_button_selected(self, index: int, selected: bool):
        self._ensure_init()
        if index < 0 or index >= len(self._buttons) or index >= len(self._config.buttons):
            pass
        else:
            pub = self._buttons[index]
            if pub.selected:
                print(f"publishing {selected} for button {index}")
                pub.selected.set(selected)

        
        if index < 0 or index >= len(self._buttons_sim) or index >= len(self._config.buttons_sim):
            pass
        else:
            pub_sim = self._buttons_sim[index]
            if pub_sim.selected:
                print(f"publishing {selected} for button {index} [SIM]")
                pub_sim.selected.set(selected)

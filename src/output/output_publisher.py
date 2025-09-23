import time
from dataclasses import dataclass
from typing import override

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

    def get_time(self) -> int:
        return time.time_ns() //1_000_000

    def _ensure_init(self):
        if not self._init_complete:
            deck_table = ntcore.NetworkTableInstance.getDefault().getTable("StreamDeck")
            self._connected = deck_table.getBooleanTopic("Connected").publish()
            self._heartbeat = deck_table.getIntegerTopic("Heartbeat").publish()

            self._buttons = []
            for i in range(self._num_buttons):
                key = self._config.buttons[i].key if i < len(self._config.buttons) else ""
                self._buttons.append(
                    ButtonPublisher(
                        key,
                        (
                            ntcore.NetworkTableInstance.getDefault()
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
                    ntcore.NetworkTableInstance.getDefault()
                    .getBooleanTopic(pub.key)
                    .publish(NTOutputPublisher.PRESSED_PUBLISH_OPTIONS)
                )

    @override
    def send_connected(self, connected: bool):
        self._ensure_init()
        self._connected.set(connected)

    @override
    def send_heartbeat(self):
        self._ensure_init()
        self._heartbeat.set(self.get_time() - self._start_time)

    @override
    def send_button_selected(self, index: int, selected: bool):
        self._ensure_init()
        if index < 0 or index >= len(self._buttons) or index >= len(self._config.buttons):
            return

        pub = self._buttons[index]
        if pub.selected:
            pub.selected.set(selected)

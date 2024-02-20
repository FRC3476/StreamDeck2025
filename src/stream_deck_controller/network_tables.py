from dataclasses import dataclass
from typing import Callable

import ntcore


@dataclass
class Button:
    key: int
    active_sub: ntcore.BooleanSubscriber
    pressed_pub: ntcore.BooleanPublisher
    icon: ntcore.StringSubscriber
    label: ntcore.StringSubscriber
    selected: bool


class NetworkTablesController:
    def __init__(self):
        self._nt = ntcore.NetworkTableInstance.getDefault().getTable("StreamDeck")
        self._buttons: dict[int, Button] = dict()
        self._button_change_handlers: dict[int, Callable[[int, bool], None]] = dict()
        self._on_connection_change: Callable[[bool], None] = lambda _: None
        self._device_connected = self._nt.getBooleanTopic("Connected").publish()
        self._last_modified = self._nt.getIntegerTopic("LastModified").subscribe(0)
        self._last_read = 0
        self._connected = False

    def bind_on_connection_change(self, change_handler: Callable[[bool], None]):
        self._on_connection_change = change_handler

    def is_connected(self):
        return self._connected

    def set_device_connected(self, connected: bool):
        self._device_connected.set(connected)

    def ensure_init(self, key):
        if key in self._buttons:
            return

        table = self._nt.getSubTable(f"Button/{key}")
        nt_key = table.getString("Key", "")
        if nt_key == "":
            return

        self._buttons[key] = Button(
            key,
            table.getBooleanTopic("Selected").subscribe(False),
            ntcore.NetworkTableInstance.getDefault().getBooleanTopic(nt_key).publish(),
            table.getStringTopic("Icon").subscribe(""),
            table.getStringTopic("Label").subscribe(""),
            table.getBoolean("Selected", False),
        )

    def bind_button(self, key: int, change_handler: Callable[[Button], None]):
        self._button_change_handlers[key] = change_handler

    def get_button(self, key: int):
        return self._buttons.get(key)

    def set_pressed(self, key: int, pressed: bool):
        if key in self._buttons:
            self._buttons[key].pressed_pub.set(pressed)

    def periodic(self):
        connected = ntcore.NetworkTableInstance.getDefault().isConnected()
        if connected != self._connected:
            self._connected = connected
            self._on_connection_change(connected)
            self._buttons.clear()
            for i in range(15):  # TOOD: Make this dynamic
                self.ensure_init(i)

        # if self._last_modified.get() != self._last_read:
        self._last_read = self._last_modified.get()
        for i in range(15):  # TOOD: Make this dynamic
            self.ensure_init(i)

        for key, button in self._buttons.items():
            selected = button.active_sub.get()
            button.selected = selected
            if key in self._button_change_handlers:
                self._button_change_handlers[key](button)

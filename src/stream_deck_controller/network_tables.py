from dataclasses import dataclass
from typing import Callable

import ntcore


@dataclass
class Button:
    active_sub: ntcore.BooleanSubscriber
    pressed_pub: ntcore.BooleanPublisher
    change_handler: Callable[[int, bool], None]
    active: bool


class NetworkTablesController:
    def __init__(self):
        self._nt = ntcore.NetworkTableInstance.getDefault().getTable("SteamDeck")
        self._buttons: dict[int, Button] = dict()
        self._on_connection_change: Callable[[bool], None] = lambda _: None
        self._device_connected = self._nt.getBooleanTopic("Connected").publish()
        self._connected = False

    def bind_on_connection_change(self, change_handler: Callable[[bool], None]):
        self._on_connection_change = change_handler

    def is_connected(self):
        return self._connected

    def set_device_connected(self, connected: bool):
        self._device_connected.set(connected)

    def ensure_init(self, key: int, change_handler: Callable[[int, bool], None]):
        if key in self._buttons:
            return True

        self._buttons[key] = Button(
            self._nt.getBooleanTopic(f"Button/{key}/Active").subscribe(False),
            self._nt.getBooleanTopic(f"Button/{key}/Pressed").publish(),
            change_handler,
            False,
        )

        return False

    def bind_button(self, key: int, change_handler: Callable[[int, bool], None]):
        if self.ensure_init(key, change_handler):
            self._buttons[key].change_handler = change_handler

    def is_active(self, key: int):
        return (key in self._buttons) and (self._buttons[key].active)

    def set_pressed(self, key: int, pressed: bool):
        self.ensure_init(key, lambda _: None)
        self._buttons[key].pressed_pub.set(pressed)

    def periodic(self):
        connected = ntcore.NetworkTableInstance.getDefault().isConnected()
        if connected != self._connected:
            self._connected = connected
            self._on_connection_change(connected)

        for key, button in self._buttons.items():
            active = button.active_sub.get()
            if active != button.active:
                button.active = active
                button.change_handler(key, active)

import os
import signal
import sys
import time
from typing import Callable

import ntcore
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.Devices import StreamDeck

from steam_deck import StreamDeckController
from network_tables import NetworkTablesController

# Folder location of image assets used by this example.
ASSETS_PATH = os.path.join(os.path.dirname(__file__), "../../assets")

_controller: StreamDeckController | None = None


def exit_gracefully(*_):
    try:
        global _controller  # pylint: disable=global-variable-not-assigned
        if _controller is not None:
            _controller.close()
        sys.exit(0)
    except:  # pylint: disable=bare-except
        sys.exit(1)


def main(retry: Callable[[], bool]):
    ntcore.NetworkTableInstance.getDefault().setServer("localhost")
    ntcore.NetworkTableInstance.getDefault().startClient4("localhost")
    nt_controller = NetworkTablesController()

    sent_search_message = False
    while retry():
        if not sent_search_message:
            print("Searching for Stream Deck...")
            sent_search_message = True

        decks: list[StreamDeck.StreamDeck] = DeviceManager().enumerate()

        if not decks:
            nt_controller.set_device_connected(False)
            time.sleep(1)
            continue

        for deck in decks:
            if not deck.is_visual():
                continue

            print(f"Creating controller for {deck.deck_type()}")

            global _controller  # pylint: disable=global-statement
            _controller = StreamDeckController(deck, nt_controller, ASSETS_PATH)
            with _controller:
                nt_controller.set_device_connected(True)
                while _controller.is_open():
                    nt_controller.periodic()
                    time.sleep(0.02)

        nt_controller.set_device_connected(False)
        sent_search_message = False
        time.sleep(1)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)
    main(lambda: True)

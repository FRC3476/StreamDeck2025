import os
import signal
import time
from typing import Callable

import ntcore
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.Devices import StreamDeck
from StreamDeck.Transport.Transport import TransportError
from config.config_source import ConfigSource, EnvironmentConfigSource, NTConfigSource
from config.config_store import ConfigStore
from output.output_publisher import NTOutputPublisher

from controller.steam_deck import StreamDeckController

DEFAULT_SERVER_IP = "10.17.1.2"
DEFAULT_ASSETS_PATH = os.path.join(os.path.dirname(__file__), "../assets")
NUM_BUTTONS = 15  # TODO: Base on deck or config

_running: bool = True


def exit_gracefully(*_):
    global _running  # pylint: disable=global-statement
    _running = False


def main(running: Callable[[], bool]):
    config = ConfigStore()
    config.server_ip = DEFAULT_SERVER_IP
    config.asset_directory = DEFAULT_ASSETS_PATH
    environment_config_source: ConfigSource = EnvironmentConfigSource()
    nt_config_source: ConfigSource = NTConfigSource(NUM_BUTTONS)

    environment_config_source.update(config)
    ntcore.NetworkTableInstance.getDefault().setServer(config.server_ip)
    ntcore.NetworkTableInstance.getDefault().startClient4(config.server_ip)
    nt_config_source.update(config)

    output_publisher = NTOutputPublisher(config, NUM_BUTTONS)

    sent_search_message = False
    while running():
        if not sent_search_message:
            print("Searching for Stream Deck...")
            sent_search_message = True

        decks: list[StreamDeck.StreamDeck] = DeviceManager().enumerate()

        nt_config_source.update(config)
        output_publisher.send_heartbeat()

        if not decks:
            output_publisher.send_connected(False)
            time.sleep(1)
            continue

        for deck in decks:
            if not deck.is_visual():
                continue

            print(f"Creating controller for {deck.deck_type()}")

            controller = StreamDeckController(deck, config, output_publisher, DEFAULT_ASSETS_PATH)
            with controller and controller:
                output_publisher.send_connected(True)

                while running() and controller.is_open():
                    nt_config_source.update(config)
                    output_publisher.send_heartbeat()
                    try:
                        controller.update()
                    except TransportError:
                        pass
                    time.sleep(0.02)

        output_publisher.send_connected(False)
        sent_search_message = False


if __name__ == "__main__":
    signal.signal(signal.SIGINT, exit_gracefully)
    main(lambda: _running)

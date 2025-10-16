import ctypes
import os
import signal
import sys
import time
from typing import Callable

from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.Devices import StreamDeck
from StreamDeck.Transport.Transport import TransportError
from config.config_source import ConfigSource, EnvironmentConfigSource, NTConfigSource
from config.config_store import ConfigStore
from output.output_publisher import NTOutputPublisher
import constants

from controller.stream_deck import StreamDeckController
from nt_instances import nt_instance
if constants.DO_SIM:
    from nt_instances import nt_instance_sim

def resource_path(filename):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, filename)
    return filename


DEFAULT_SERVER_IP = "10.34.76.2"
DEFAULT_SERVER_IP_SIM = "127.0.0.1" # for sim
DEFAULT_ASSETS_PATH = os.path.join(os.path.dirname(__file__), "../assets")
MIN_LOOP_TIME = 0.02

ctypes.CDLL(resource_path(os.path.join(DEFAULT_ASSETS_PATH, "dlls", "hidapi.dll")))

_running: bool = True
    

def exit_gracefully(*_):
    global _running  # pylint: disable=global-statement
    _running = False


def main(running: Callable[[], bool]):
    config = ConfigStore()
    config.server_ip = DEFAULT_SERVER_IP
    config.server_ip_sim = DEFAULT_SERVER_IP_SIM
    environment_config_source: ConfigSource = EnvironmentConfigSource()

    environment_config_source.update(config)
    
    nt_instance.setServer(config.server_ip)
    nt_instance.startClient4(config.server_ip)

    if constants.DO_SIM:
        nt_instance_sim.setServer(config.server_ip_sim)
        nt_instance_sim.startClient4(config.server_ip_sim)
    
    nt_config_source: ConfigSource = NTConfigSource(constants.NUM_BUTTONS*constants.NUM_PAGES)
    nt_config_source.update(config)

    output_publisher = NTOutputPublisher(config, constants.NUM_BUTTONS*constants.NUM_PAGES)

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

                last_time = time.time()
                while running() and controller.is_open():
                    nt_config_source.update(config)
                    output_publisher.send_heartbeat()
                    try:
                        controller.update()
                    except TransportError:
                        pass

                    new_time = time.time()
                    d_time = new_time - last_time
                    if d_time < MIN_LOOP_TIME:
                        time.sleep(MIN_LOOP_TIME - d_time)
                    last_time = new_time

        output_publisher.send_connected(False)
        sent_search_message = False


if __name__ == "__main__":
    signal.signal(signal.SIGINT, exit_gracefully)
    main(lambda: _running)

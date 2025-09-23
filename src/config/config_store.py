from dataclasses import dataclass, field
from typing import Optional
import constants

@dataclass
class ButtonConfig:
    key: str = ""
    selected: bool = False
    active_background: str = constants.COLORS.BLACK
    inactive_background: str = constants.COLORS.BLACK
    active_foreground: str = constants.COLORS.WHITE
    inactive_foreground: str = constants.COLORS.WHITE
    active_text: str = ""
    inactive_text: str = ""


@dataclass
class ConfigStore:
    server_ip: str = ""
    asset_directory: str = ""
    remote_connected: bool = False
    buttons: list[ButtonConfig] = field(default_factory=lambda: [])

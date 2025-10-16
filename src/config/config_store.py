from dataclasses import dataclass, field
from typing import Optional

@dataclass
class ButtonConfig:
    key: str = ""
    selected: bool = False
    active_background: str = ""
    inactive_background: str = ""
    active_foreground: str = ""
    inactive_foreground: str = ""
    active_text: str = ""
    inactive_text: str = ""

@dataclass
class ConfigStore:
    server_ip: str = ""
    server_ip_sim: str = ""
    remote_connected: bool = False
    remote_connected_sim: bool = False
    buttons: list[ButtonConfig] = field(default_factory=lambda: [])
    buttons_sim: list[ButtonConfig] = field(default_factory=lambda: [])
    page: int = 0
    page_button: Optional[ButtonConfig] = None
    page_button_index: Optional[int] = None
    page_button_sim: Optional[ButtonConfig] = None
    page_button_index_sim: Optional[int] = None

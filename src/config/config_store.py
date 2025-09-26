from dataclasses import dataclass, field

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
    asset_directory: str = ""
    remote_connected: bool = False
    remote_connected_sim: bool = False
    buttons: list[ButtonConfig] = field(default_factory=lambda: [])
    buttons_sim: list[ButtonConfig] = field(default_factory=lambda: [])

from dataclasses import dataclass, field


@dataclass
class ButtonConfig:
    key: str = ""
    selected: bool = False
    icon: str = ""
    label: str = ""


@dataclass
class ConfigStore:
    server_ip: str = ""
    asset_directory: str = ""
    remote_connected: bool = False
    buttons: list[ButtonConfig] = field(default_factory=lambda: [])

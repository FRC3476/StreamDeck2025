from dataclasses import dataclass

KEY_SPACING = (36, 36)
DO_SIM = False

BACKGROUND_IMAGE = "JAWS_logo.jpg"
TEXT_HEIGHT_OFFSET = 5

@dataclass
class COLORS:
    CO_ORANGE = "#FF7A1C"
    CO_TEAL = "#209299"
    WHITE = "#FFFFFF"
    BLACK = "#000000"
    RED = "#FF0000"
    GREEN = "#00FF00"
    BLUE = "#0000FF"
    CYAN = "#00FFFF"
    MAGENTA = "#FF00FF"
    YELLOW = "#FFFF00"
    DEFAULT_BACKGROUND = BLACK
    DEFAULT_FOREGROUND = WHITE
    NO_CONFIG = YELLOW
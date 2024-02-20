import os

from matplotlib import font_manager
from PIL import Image, ImageDraw, ImageFont, ImageOps
from StreamDeck.Devices.StreamDeck import StreamDeck
from StreamDeck.ImageHelpers import PILHelper
from StreamDeck.Transport.Transport import TransportError

import image_util
from network_tables import Button, NetworkTablesController

KEY_SPACING = (36, 36)
BACKGROUND_COLOR = "#9D2235"
BACKGROUND_IMAGE = "Decepticub.png"
ACTIVE_COLOR = BACKGROUND_COLOR
NOT_ACTIVE_COLOR = "#424242"


class StreamDeckController:
    def __init__(self, deck: StreamDeck, nt_controller: NetworkTablesController, assets_path: str):
        self._deck = deck
        self._nt_controller = nt_controller
        self._assets_path = assets_path
        self._default_background = self.generate_key_images_from_deck_sized_image(BACKGROUND_IMAGE)

        font = font_manager.FontProperties(family="Arial")
        file = font_manager.findfont(font)
        self._default_font = ImageFont.truetype(file, 14)

    def __enter__(self):
        self.open()

    def __exit__(self, *_):
        try:
            self.close()
        except TransportError:  # pylint: disable=bare-except
            pass

    def create_full_deck_sized_image(self, image_filename: str):
        """Generates an image that is correctly sized to fit across all keys"""
        key_rows, key_cols = self._deck.key_layout()
        key_width, key_height = self._deck.key_image_format()["size"]
        spacing_x, spacing_y = KEY_SPACING

        key_width *= key_cols
        key_height *= key_rows

        spacing_x *= key_cols - 1
        spacing_y *= key_rows - 1

        full_deck_image_size = (key_width + spacing_x, key_height + spacing_y)

        # Create a filled version of the image in the correct aspect ratio and then resize it to fit the full deck
        foreground = Image.open(os.path.join(self._assets_path, image_filename)).convert("RGBA")
        filled_foreground = Image.new(
            "RGBA",
            (
                int(foreground.height * full_deck_image_size[0] / full_deck_image_size[1]),
                foreground.height,
            ),
            color=BACKGROUND_COLOR,
        )
        filled_foreground.paste(
            foreground,
            (int((filled_foreground.width - foreground.width) / 2), 0),
            foreground,
        )

        return ImageOps.fit(
            filled_foreground,
            full_deck_image_size,
            Image.Resampling.LANCZOS,
        )

    def crop_key_image_from_deck_sized_image(self, image: Image, key: int):
        """Crops out a key-sized image from a larger deck-sized image"""
        _, key_cols = self._deck.key_layout()
        key_width, key_height = self._deck.key_image_format()["size"]
        spacing_x, spacing_y = KEY_SPACING

        row = key // key_cols
        col = key % key_cols

        start_x = col * (key_width + spacing_x)
        start_y = row * (key_height + spacing_y)

        region = (start_x, start_y, start_x + key_width, start_y + key_height)
        segment = image.crop(region)

        key_image = PILHelper.create_key_image(self._deck)
        key_image.paste(segment)

        return PILHelper.to_native_key_format(self._deck, key_image)

    def generate_key_images_from_deck_sized_image(self, image_filename: str):
        """Creates a dictionary of key images by key from a full-deck image"""
        image = self.create_full_deck_sized_image(image_filename)

        print(f"Created full deck image size of {image.width}x{image.height} pixels.")

        key_images = dict()
        for k in range(self._deck.key_count()):
            key_images[k] = self.crop_key_image_from_deck_sized_image(image, k)

        return key_images

    def render_all_keys(self, key_images: dict):
        for k in range(self._deck.key_count()):
            key_image = key_images[k]
            self._deck.set_key_image(k, key_image)

    def render_default_background(self):
        self.render_all_keys(self._default_background)

    def render_key(self, icon_filename: str, label_text: str, background: str):
        image = None
        if icon_filename != "":
            icon_path = os.path.join(self._assets_path, icon_filename + ".svg")
            icon = image_util.image_from_svg(icon_path, 48)
            image = PILHelper.create_scaled_key_image(self._deck, icon, margins=[0, 0, 20, 0], background=background)
        else:
            image = PILHelper.create_key_image(self._deck, background=background)

        draw = ImageDraw.Draw(image)
        draw.text(
            (image.width / 2, image.height - 5),
            text=label_text,
            font=self._default_font,
            anchor="ms",
            fill="white",
        )

        return PILHelper.to_native_key_format(self._deck, image)

    def set_key_empty(self, key: int):
        image = PILHelper.create_key_image(self._deck, background=NOT_ACTIVE_COLOR)
        self._deck.set_key_image(key, PILHelper.to_native_key_format(self._deck, image))

    def set_key_image(self, button: Button):
        background = ACTIVE_COLOR if button.selected else NOT_ACTIVE_COLOR
        image = self.render_key(button.icon.get(), button.label.get(), background)
        self._deck.set_key_image(button.key, image)

    def on_key_change(self, _, key: int, state: bool):
        print(f"{self._deck.get_serial_number()} Key {key} = {state}", flush=True)
        self._nt_controller.set_pressed(key, state)

    def on_connection_change(self, connected: bool):
        if not connected:
            self.render_default_background()
            return

        self._deck.reset()
        for key in range(self._deck.key_count()):
            button = self._nt_controller.get_button(key)
            if button is None:
                self.set_key_empty(key)
            else:
                self.set_key_image(button)

    def is_open(self) -> bool:
        return self._deck.is_open()

    def close_deck(self):
        if self._deck.is_open():
            self.render_default_background()
            self._deck.close()
            print(f"Closed {self._deck.deck_type()}")

    def open(self):
        self._deck.open()

        print(
            f"Opened {self._deck.deck_type()} (sn: '{self._deck.get_serial_number()}', fw: '{self._deck.get_firmware_version()}')"
        )

        self._deck.set_brightness(80)

        self._nt_controller.bind_on_connection_change(self.on_connection_change)
        for key in range(self._deck.key_count()):
            self._nt_controller.bind_button(key, self.set_key_image)

        self.on_connection_change(self._nt_controller.is_connected())

        self._deck.set_key_callback(self.on_key_change)

    def close(self):
        self.close_deck()

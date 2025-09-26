import os

from matplotlib import font_manager
from PIL import Image, ImageDraw, ImageFont, ImageOps
from StreamDeck.Devices.StreamDeck import StreamDeck
from StreamDeck.ImageHelpers import PILHelper
from StreamDeck.Transport.Transport import TransportError
from config.config_store import ButtonConfig, ConfigStore

from output.output_publisher import OutputPublisher
import constants

class StreamDeckController:
    def __init__(self, deck: StreamDeck, config: ConfigStore, output_publisher: OutputPublisher, assets_path: str):
        self._deck = deck
        self._config = config
        self._output_publisher = output_publisher
        self._assets_path = assets_path
        self._default_background = self.generate_key_images_from_deck_sized_image(constants.BACKGROUND_IMAGE)
        self._icon_cache: dict[tuple[str, str, str], Image.Image] = dict()
        self._last_images: list[tuple[str, any]] = [("none", None)] * deck.key_count()

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
        spacing_x, spacing_y = constants.KEY_SPACING

        key_width *= key_cols
        key_height *= key_rows

        spacing_x *= key_cols - 1
        spacing_y *= key_rows - 1

        full_deck_image_size = (key_width + spacing_x, key_height + spacing_y)

        # Create a filled version of the image in the correct aspect ratio and then resize it to fit the full deck
        foreground = Image.open(os.path.join(self._assets_path, image_filename)).convert("RGBA")
        image = Image.new(
            "RGBA",
            (
                foreground.height * full_deck_image_size[0] // full_deck_image_size[1],
                foreground.height,
            ),
            color=constants.COLORS.DEFAULT_BACKGROUND,
        )
        image.paste(
            foreground,
            ((image.width - foreground.width) // 2, 0),
            foreground,
        )

        return ImageOps.fit(
            image,
            full_deck_image_size,
            Image.Resampling.LANCZOS,
        )

    def crop_key_image_from_deck_sized_image(self, image: Image, key: int):
        """Crops out a key-sized image from a larger deck-sized image"""
        _, key_cols = self._deck.key_layout()
        key_width, key_height = self._deck.key_image_format()["size"]
        spacing_x, spacing_y = constants.KEY_SPACING

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

            unique_key = ("render_all", None)
            if self._last_images[k] != unique_key:
                self._deck.set_key_image(k, key_image)
                self._last_images[k] = unique_key

    def render_default_background(self):
        self.render_all_keys(self._default_background)

    def render_key(self, background: str, foreground: str, text: str):
        cache_key = (background, foreground, text)
        if cache_key in self._icon_cache:
            return PILHelper.to_native_key_format(self._deck, self._icon_cache[cache_key])

        image = PILHelper.create_key_image(self._deck, background=background)

        draw = ImageDraw.Draw(image)
        draw.text(
            (image.width / 2, image.height - constants.TEXT_HEIGHT_OFFSET),
            text=text,
            font=self._default_font,
            anchor="ms",
            fill=foreground,
        )

        self._icon_cache[cache_key] = image
        return PILHelper.to_native_key_format(self._deck, image)

    def set_key_empty(self, key: int):
        image = PILHelper.create_key_image(self._deck, background=constants.COLORS.NO_CONFIG)

        unique_key = ("empty_key", None)
        if self._last_images[key] != unique_key:
            self._deck.set_key_image(key, PILHelper.to_native_key_format(self._deck, image))
            self._last_images[key] = unique_key

    def set_key_image(self, key: int, button: ButtonConfig):
        if button.selected:
            background = button.active_background if button.active_background != "" else constants.COLORS.DEFAULT_BACKGROUND
            foreground = button.active_foreground if button.active_foreground != "" else constants.COLORS.DEFAULT_FOREGROUND
            text = button.active_text
        else:
            background = button.inactive_background if button.inactive_background != "" else constants.COLORS.DEFAULT_BACKGROUND
            foreground = button.inactive_foreground if button.inactive_foreground != "" else constants.COLORS.DEFAULT_FOREGROUND
            text = button.inactive_text
        image = self.render_key(background, foreground, text)

        unique_key = ("render_key", (background, foreground, text))
        if self._last_images[key] != unique_key:
            self._deck.set_key_image(key, image)
            self._last_images[key] = unique_key

    def on_key_change(self, _, key: int, selected: bool):
        print(f"{self._deck.get_serial_number()} Key {key} = {selected}", flush=True)
        self._output_publisher.send_button_selected(key, selected)

    def update(self):
        # TODO: Only send images on changes
        if not self._config.remote_connected and not self._config.remote_connected_sim:
            self.render_default_background()
            return


        for key in range(self._deck.key_count()):
            if key < len(self._config.buttons):
                if (self._config.buttons[key].active_background == "" and 
                    self._config.buttons[key].inactive_background == "" and 
                    self._config.buttons[key].active_foreground == "" and 
                    self._config.buttons[key].inactive_foreground == "" and 
                    self._config.buttons[key].active_text == "" and 
                    self._config.buttons[key].inactive_text == ""):
                    button = self._config.buttons_sim[key]
                else:
                    button = self._config.buttons[key]
            else:
                button = None
            if button is None:
                self.set_key_empty(key)
            else:
                self.set_key_image(key, button)

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
            "Opened {} (sn: '{}', fw: '{}')".format(
                self._deck.deck_type(), self._deck.get_serial_number(), self._deck.get_firmware_version()
            )
        )

        self._deck.set_brightness(80)
        self._deck.set_key_callback(self.on_key_change)

        self.update()

    def close(self):
        self.close_deck()

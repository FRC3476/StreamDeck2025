import io
import logging

import skia
from PIL import Image


def image_from_svg(file: str, element_size: int):
    try:
        stream = skia.FILEStream.Make(file)
        svg = skia.SVGDOM.MakeFromStream(stream)
        stream.close()
        width, height = svg.containerSize()
        if not width or not height:
            svg.setContainerSize(skia.Size.Make(element_size, element_size))
            width, height = element_size, element_size
        surface = skia.Surface(element_size, element_size)
        with surface as canvas:
            canvas.scale(element_size / width, element_size / height)
            svg.render(canvas)
        with io.BytesIO(surface.makeImageSnapshot().encodeToData()) as f:
            image = Image.open(f).copy()
            print(f"Loaded {file}")
            return image
    except Exception as error:  # pylint: disable=broad-exception-caught
        logging.getLogger(__name__).exception(error)

    print(f"Failed to load file {file}")
    return Image.new("RGBA", (element_size, element_size), (255, 0, 0, 0))


def color_image(foreground: Image, color: any):
    colored_foreground = Image.new(
        "RGBA",
        (
            foreground.width,
            foreground.height,
        ),
        color=color,
    )
    image = Image.new("RGBA", (foreground.width, foreground.height), (255, 0, 0, 0))
    image.paste(
        colored_foreground,
        (0, 0),
        foreground,
    )
    return image

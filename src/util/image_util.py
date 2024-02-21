import io

import skia
from PIL import Image

images = dict()


def image_from_svg(file: str, element_size: int):
    stream = skia.FILEStream.Make(file)
    svg = skia.SVGDOM.MakeFromStream(stream)
    stream.close()
    width, height = svg.containerSize()
    surface = skia.Surface(element_size, element_size)
    with surface as canvas:
        canvas.scale(element_size / width, element_size / height)
        svg.render(canvas)
    with io.BytesIO(surface.makeImageSnapshot().encodeToData()) as f:
        image = Image.open(f).copy()
        images[file] = image
        return image

from PIL.Image import Image

from collections.abc import Collection
from io import BufferedIOBase


def process_image(image: Image) -> Image:
    image_w_palette = image.quantize()

    palette = image_w_palette.palette.colors
    transparent_color = min(palette, key=lambda x: x[3])
    if transparent_color[3] == 255:
        # don't set a transparent color if there are no transparent colors
        return image_w_palette

    transparent_index = palette[transparent_color]

    image_w_palette.info["transparency"] = transparent_index
    image_w_palette.info["background"] = transparent_index

    return image_w_palette


def save_transparent_gif(images: Collection[Image], durations: int | Collection[int], save_file: BufferedIOBase):
    first_image, *remaining_images = map(process_image, images)

    first_image.save(
        save_file,
        format="GIF",
        save_all=True,
        append_images=remaining_images,
        duration=durations,
        disposal=2,
        loop=0
    )
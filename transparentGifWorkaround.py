from PIL.Image import Image
import numpy as np

from collections.abc import Collection
from functools import partial
from io import BufferedIOBase


def process_image(image, alpha_threshold=0) -> Image:
    image_w_palette = image.convert("P", colors=256-1)

    palette_indices = np.frombuffer(bytearray(image_w_palette.tobytes()), "uint8")

    image_data = np.array(image)
    palette_indices[image_data.reshape(-1, 4)[:, 3] <= alpha_threshold] = 0xff

    image_w_palette.frombytes(palette_indices.tobytes())
    image_w_palette.info["transparency"] = 0xff
    image_w_palette.info["background"] = 0xff

    return image_w_palette


def save_transparent_gif(images: Collection[Image], durations, save_file, alpha_threshold=0):
    first_image, *remaining_images = map(
        partial(process_image, alpha_threshold=alpha_threshold),
        images
    )

    first_image.save(
        save_file,
        format="GIF",
        save_all=True,
        append_images=remaining_images,
        duration=durations,
        disposal=2,
        loop=0
    )
import cm2py as cm2
import math
from PIL import Image


def image(im: Image.Image, size: int, transparency: bool):
    largestDim = max(im.width, im.height)
    scale = size / largestDim
    dim = (int(im.width * scale), int(im.height * scale))
    im = im.resize(dim)
    im = im.convert("RGBA")
    pixels = list(im.getdata())

    save = cm2.Save()

    for y in range(dim[1] - 1, -1, -1):
        for x in range(dim[0]):
            pixel_index = y * dim[0] + x
            if pixel_index < len(pixels):
                pixel = pixels[pixel_index]
                alpha = round(pixel[3] * (100 / 255))
                if alpha < 5 and transparency:
                    continue
                if alpha < 95 and transparency:
                    save.addBlock(
                        cm2.LED,
                        (x, dim[1] - 1 - y, 0),
                        properties=[pixel[0], pixel[1], pixel[2], 100, alpha],
                    )
                else:
                    save.addBlock(
                        cm2.TILE,
                        (x, dim[1] - 1 - y, 0),
                        properties=[pixel[0], pixel[1], pixel[2]],
                    )

    return save

import cm2py as cm2
import math
from PIL import Image

def image(im: Image.Image, size):
    largestDim = max(im.width, im.height)
    scale = size/largestDim
    dim = (im.width*scale, im.height*scale)
    im = im.resize(dim)
    pixels = list(im.getdata())

    print(pixels)

    save = cm2.Save()

    return save
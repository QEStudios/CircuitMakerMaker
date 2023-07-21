import cm2py as cm2
import numpy as np
import math
from io import BytesIO
from PIL import Image, ImageDraw
import asyncio


async def render(saveString):
    save = cm2.importSave(saveString, snapToGrid=False)

    size = (1600, 1200)
    angle = [0,0]

    blockColours = [
        (255, 9, 0),
        (0, 121, 255),
        (0, 241, 29),
        (168, 0, 255),
        (255, 127, 0),
        (30, 30, 30),
        (175, 175, 175),
        (175, 131, 76),
        (73, 185, 255),
        (255, 72, 72),
        (0, 42, 89),
        (213, 0, 103),
        (84, 54, 35),
        (25, 71, 84),
    ]

    sqrt3 = math.sqrt(3)
    sqrt2 = math.sqrt(2)
    def project(points):
        if angle[1] == 0:
            matrix = np.array([
                [sqrt3, 0, -sqrt3],
                [1, 2, 1],
                [sqrt2, -sqrt2, sqrt2]], dtype=float)
        projected = np.dot(matrix, points.T).T
        projected[:, 1] *= -1
        return projected

    def drawBlock(b, p):
        print(b.blockId, b.properties)
        blockColour = blockColours[b.blockId]
        if b.blockId == cm2.LED and len(b.properties) == 3:
            blockColour = tuple([int(v) for v in b.properties])
        x = p[0]*scale + size[0]/2 - bounds[0][0]*scale - sizeX/2*scale
        y = p[1]*scale + size[1]/2 - bounds[1][0]*scale - sizeY/2*scale
        if angle[1] == 0:
            draw.polygon([
                (x-sqrt3*scale,y-scale),
                (x,y-2*scale),
                (x+sqrt3*scale,y-scale),
                (x,y)], fill=blockColour)

            draw.polygon([
                (x,y),
                (x+sqrt3*scale,y-scale),
                (x+sqrt3*scale,y+scale),
                (x,y+2*scale)], fill=tuple([int(v*.85) for v in blockColour]))
        
            draw.polygon([
                (x,y+2*scale),
                (x-sqrt3*scale,y+scale),
                (x-sqrt3*scale,y-scale),
                (x,y)], fill=tuple([int(v*.75) for v in blockColour]))
            draw.line([
                (x-sqrt3*scale,y-scale),
                (x,y-2*scale),
                (x+sqrt3*scale,y-scale),
                (x+sqrt3*scale,y+scale),
                (x,y+2*scale),
                (x-sqrt3*scale,y+scale),
                (x-sqrt3*scale,y-scale),
                (x,y),
                (x+sqrt3*scale,y-scale)], fill=0, width=int(scale/6), joint="curve")
            draw.line([
                (x,y),
                (x,y+2*scale)], fill=0, width=int(scale/6), joint="curve")

    positions = [(b.x, b.y, 0-b.z) for b in save.blocks]
    points = np.array(positions)
    interPoints = project(points)
    pointIndices = np.flip(np.argsort(interPoints[:, 2]))
    projectedPoints = interPoints[pointIndices]
    sortedBlocks = np.array(save.blocks)[pointIndices]

    bounds = [[projectedPoints[0][0], projectedPoints[0][0]], [projectedPoints[0][1], projectedPoints[0][1]]]

    for p in projectedPoints:
        if p[0] < bounds[0][0]:
            bounds[0][0] = p[0]
        if p[0] > bounds[0][1]:
            bounds[0][1] = p[0]
        
        if p[1] < bounds[1][0]:
            bounds[1][0] = p[1]
        if p[1] > bounds[1][1]:
            bounds[1][1] = p[1]

    bounds[0][0] -= 3
    bounds[0][1] += 3
    bounds[1][0] -= 3
    bounds[1][1] += 3

    sizeX = bounds[0][1] - bounds[0][0]
    sizeY = bounds[1][1] - bounds[1][0]

    scaleX = int(size[0] / sizeX)
    scaleY = int(size[1] / sizeY)

    scale = min(scaleX, scaleY)


    im = Image.new("RGB", (size[0], size[1]), color=(255,255,255))
    draw = ImageDraw.Draw(im)

    for i in range(len(projectedPoints)):
        b = sortedBlocks[i]
        p = projectedPoints[i]
        drawBlock(b, p)

    stream = BytesIO()
    im.save(stream, "PNG")
    stream.seek(0)
    return stream, save

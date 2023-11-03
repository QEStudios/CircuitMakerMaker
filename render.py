import cm2py as cm2
import numpy as np
import math
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import random
import asyncio
from transparentGifWorkaround import save_transparent_gif

async def render(saveString, messageId):
    def project(points, rot):
        a = math.asin(math.tan(math.radians(30)))
        b = math.radians(rot)
        aMatrix = np.array([
            [1, 0, 0],
            [0, math.cos(a), math.sin(a)],
            [0, -math.sin(a), math.cos(a)],
        ], dtype=float)
        bMatrix = np.array([
            [math.cos(b), 0, -math.sin(b)],
            [0, 1, 0],
            [math.sin(b), 0, math.cos(b)]
        ], dtype=float)
        matrix = np.matmul(aMatrix, bMatrix) * math.sqrt(6)
        projected = np.dot(matrix, points.T).T
        projected[:, 1] *= -1
        return projected

    def generateText(text):
        fnt = ImageFont.truetype('SourceCodePro-Medium.ttf', 72)
        size, offset = fnt.font.getsize(text)
        img = Image.new('RGBA', size, (0,0,0,255))
        draw.text(offset, text, (255, 255, 255), font=fnt)
        return img

    def drawBlock(b, p):
        if b.state == True:
            blockColour = tuple((np.array(blockColours[b.blockId]) + np.array([64,64,64])).tolist())
        else:
            blockColour = blockColours[b.blockId]
        if (b.blockId == cm2.LED or b.blockId == cm2.TILE) and b.properties and len(b.properties) == 3:
            blockColour = tuple([int(v) for v in b.properties])
        if b.blockId == cm2.LED and b.state == False:
            imMask = Image.new('RGBA', size)
            thisDraw = ImageDraw.Draw(imMask)
            transparency = [127]
        else:
            thisDraw = draw
            transparency = []
        
        x = p[0]*scale + size[0]/2
        y = p[1]*scale + size[1]/2
        posArray = np.column_stack((np.repeat(x, 8), np.repeat(y, 8)))
        pCube = [tuple(v) for v in (projectedCube[:, :2] + posArray).tolist()]
        sideShades = [0.85, 0.75, 0.6, 0.7]
        thisDraw.polygon([
            pCube[3],
            pCube[2],
            pCube[6],
            pCube[7]], fill=tuple(list(blockColour) + transparency))

        thisDraw.polygon([
            pCube[1],
            pCube[0],
            pCube[2],
            pCube[3]], fill=tuple([int(v*sideShades[(angle//90)%4]) for v in blockColour] + transparency))

        thisDraw.polygon([
            pCube[2],
            pCube[0],
            pCube[4],
            pCube[6]], fill=tuple([int(v*sideShades[(angle//90+1)%4]) for v in blockColour] + transparency))

        # thisDraw.line([
        #     pCube[0],
        #     pCube[4],
        #     pCube[6],
        #     pCube[7],
        #     pCube[3],
        #     pCube[1],
        #     pCube[0],
        #     pCube[2],
        #     pCube[6]], fill=0, width=int(scale/8), joint="curve")
        # thisDraw.line([
        #     pCube[2],
        #     pCube[3]], fill=0, width=int(scale/8), joint="curve")

        if b.blockId == cm2.LED and b.state == False:
            im.alpha_composite(imMask, (0, 0))
        
        if b.blockId == cm2.TEXT:
            im.paste(generateText("A"), (0,0))

    save = cm2.importSave(saveString, snapToGrid=False)

    size = (600, 450)

    scale = -1
    bounds = []

    center = np.array([0,0,0], dtype="float64")

    for b in save.blocks.values():
        center += np.array(b.pos)

    center = (center / len(save.blocks)).tolist()

    positions = [(b.x - center[0], b.y - center[1], center[2]-b.z) for b in save.blocks.values()]
    points = np.array(positions)

    projectedPointsList = []
    sortedBlocksList = []

    for r in range(0,36):
        angle = r * 10 + 5
        interPoints = project(points, angle)
        pointIndices = np.flip(np.argsort(interPoints[:, 2]))
        projectedPoints = interPoints[pointIndices]
        sortedBlocks = np.array(list(save.blocks.values()))[pointIndices]

        projectedPointsList.append(projectedPoints)
        sortedBlocksList.append(sortedBlocks)

    for i in range(0,36):
        projectedPoints = projectedPointsList[i]

        angle = i * 10 + 18
        
        tmpBounds = [[projectedPoints[0][0], projectedPoints[0][0]], [projectedPoints[0][1], projectedPoints[0][1]]]

        for p in projectedPoints:
            if p[0] < tmpBounds[0][0]:
                tmpBounds[0][0] = p[0]
            if p[0] > tmpBounds[0][1]:
                tmpBounds[0][1] = p[0]
            
            if p[1] < tmpBounds[1][0]:
                tmpBounds[1][0] = p[1]
            if p[1] > tmpBounds[1][1]:
                tmpBounds[1][1] = p[1]

        tmpBounds[0][0] -= 5
        tmpBounds[0][1] += 5
        tmpBounds[1][0] -= 5
        tmpBounds[1][1] += 5

        sizeX = tmpBounds[0][1] - tmpBounds[0][0]
        sizeY = tmpBounds[1][1] - tmpBounds[1][0]

        scaleX = size[0] / sizeX
        scaleY = size[1] / sizeY

        tmpScale = min(min(scaleX, scaleY), min(size[0]*0.2, size[1]*0.2))

        if scale > tmpScale or scale == -1:
            scale = tmpScale
            bounds = tmpBounds

    frames = []

    for i in range(0,36):
        projectedPoints = projectedPointsList[i]
        sortedBlocks = sortedBlocksList[i]

        angle = i * 10 + 5

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
            (75, 75, 75)
        ]

        interPoints = project(points, angle)
        pointIndices = np.flip(np.argsort(interPoints[:, 2]))
        projectedPoints = interPoints[pointIndices]
        

        cubePoints = np.array([
            [-0.5,-0.5,-0.5],
            [0.5,-0.5,-0.5],
            [-0.5,0.5,-0.5],
            [0.5,0.5,-0.5],
            [-0.5,-0.5,0.5],
            [0.5,-0.5,0.5],
            [-0.5,0.5,0.5],
            [0.5,0.5,0.5],
        ]) * scale
        projectedCube = project(cubePoints, angle % 90)

        im = Image.new("RGBA", (size[0], size[1]), color=(0,0,0,0))
        draw = ImageDraw.Draw(im)

        for i in range(len(projectedPoints)):
            b = sortedBlocks[i]
            p = projectedPoints[i]
            drawBlock(b, p)
    
        frames.append(im)

    outputFilename = f"result{messageId}.gif"
    with open(outputFilename, "wb") as f:
        save_transparent_gif(images=frames, save_file=f, durations=100)
    return outputFilename, save

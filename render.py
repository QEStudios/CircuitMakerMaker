import cm2py as cm2
import numpy as np
import math
from io import BytesIO
from PIL import Image, ImageDraw
import random
import asyncio


async def render(saveString):
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

    def drawBlock(b, p):
        if b.state == True:
            blockColour = tuple((np.array(blockColours[b.blockId]) + np.array([64,64,64])).tolist())
        else:
            blockColour = blockColours[b.blockId]
        if b.blockId == cm2.LED and b.properties and len(b.properties) == 3:
            blockColour = tuple([int(v) for v in b.properties])
        x = p[0]*scale + size[0]/2
        y = p[1]*scale + size[1]/2
        posArray = np.column_stack((np.repeat(x, 8), np.repeat(y, 8)))
        pCube = [tuple(v) for v in (projectedCube[:, :2] + posArray).tolist()]
        sideShades = [0.85, 0.75, 0.6, 0.7]
        draw.polygon([
            pCube[3],
            pCube[2],
            pCube[6],
            pCube[7]], fill=blockColour)

        draw.polygon([
            pCube[1],
            pCube[0],
            pCube[2],
            pCube[3]], fill=tuple([int(v*sideShades[(angle//90)%4]) for v in blockColour]))

        draw.polygon([
            pCube[2],
            pCube[0],
            pCube[4],
            pCube[6]], fill=tuple([int(v*sideShades[(angle//90+1)%4]) for v in blockColour]))

        # draw.line([
        #     pCube[0],
        #     pCube[4],
        #     pCube[6],
        #     pCube[7],
        #     pCube[3],
        #     pCube[1],
        #     pCube[0],
        #     pCube[2],
        #     pCube[6]], fill=0, width=int(scale/8), joint="curve")
        # draw.line([
        #     pCube[2],
        #     pCube[3]], fill=0, width=int(scale/8), joint="curve")
    save = cm2.importSave(saveString, snapToGrid=False)

    size = (600, 450)

    scale = -1
    bounds = []

    physicalBounds = [[save.blocks[0].pos[0],save.blocks[0].pos[0]], [save.blocks[0].pos[1],save.blocks[0].pos[1]], [save.blocks[0].pos[2],save.blocks[0].pos[2]]]

    for p in [b.pos for b in save.blocks]:
        if p[0] < physicalBounds[0][0]:
            physicalBounds[0][0] = p[0]
        if p[0] > physicalBounds[0][1]:
            physicalBounds[0][1] = p[0]
        
        if p[1] < physicalBounds[1][0]:
            physicalBounds[1][0] = p[1]
        if p[1] > physicalBounds[1][1]:
            physicalBounds[1][1] = p[1]
        
        if p[2] < physicalBounds[2][0]:
            physicalBounds[2][0] = p[2]
        if p[2] > physicalBounds[2][1]:
            physicalBounds[2][1] = p[2]

    center = [
        physicalBounds[0][0] + (physicalBounds[0][1] - physicalBounds[0][0])/2,
        physicalBounds[1][0] + (physicalBounds[1][1] - physicalBounds[1][0])/2,
        physicalBounds[2][0] + (physicalBounds[2][1] - physicalBounds[2][0])/2,
    ]

    print(physicalBounds)

    print(center)

    print((0 - center[0], 0 - center[1], center[2]-0))

    positions = [(b.x - center[0], b.y - center[1], center[2]-b.z) for b in save.blocks]
    points = np.array(positions)

    projectedPointsList = []
    sortedBlocksList = []

    for r in range(0,36):
        angle = r * 10 + 5
        interPoints = project(points, angle)
        pointIndices = np.flip(np.argsort(interPoints[:, 2]))
        projectedPoints = interPoints[pointIndices]
        sortedBlocks = np.array(save.blocks)[pointIndices]

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

        tmpBounds[0][0] -= (tmpBounds[0][1] - tmpBounds[0][0])*0.1
        tmpBounds[0][1] += (tmpBounds[0][1] - tmpBounds[0][0])*0.1
        tmpBounds[1][0] -= (tmpBounds[1][1] - tmpBounds[1][0])*0.1
        tmpBounds[1][1] += (tmpBounds[1][1] - tmpBounds[1][0])*0.1

        sizeX = tmpBounds[0][1] - tmpBounds[0][0]
        sizeY = tmpBounds[1][1] - tmpBounds[1][0]

        scaleX = size[0] / sizeX
        scaleY = size[1] / sizeY

        tmpScale = min(scaleX, scaleY)

        if scale > tmpScale or scale == -1:
            scale = tmpScale
            bounds = tmpBounds

    sizeX = bounds[0][1] - bounds[0][0]
    sizeY = bounds[1][1] - bounds[1][0]

    scaleX = size[0] / sizeX
    scaleY = size[1] / sizeY

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
        ]

        sqrt3 = math.sqrt(3)
        sqrt2 = math.sqrt(2)

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

        im = Image.new("RGB", (size[0], size[1]), color=(255,255,255))
        draw = ImageDraw.Draw(im)

        for i in range(len(projectedPoints)):
            b = sortedBlocks[i]
            p = projectedPoints[i]
            drawBlock(b, p)
    
        frames.append(im)

    stream = BytesIO()
    frames[0].save(stream, "GIF", save_all=True, append_images=frames[1:], optimize=True, duration=1.5, loop=0)
    stream.seek(0)
    return stream, save

import cm2py as cm2
import math

def chain(period):
    save = cm2.Save()
    blocks = []
    for i in range(math.ceil(period / 2)):
        blocks.append(save.addBlock(cm2.OR, (i,0,0)))
        if len(blocks) > 1:
            save.addConnection(blocks[-2], blocks[-1])
    for i in range(period // 2):
        blocks.append(save.addBlock(cm2.OR, (period // 2 - i - 1,0,1)))
        save.addConnection(blocks[-2], blocks[-1])
    save.addConnection(blocks[-1], blocks[0])
    blocks[0].state = True
    return save

def cycle(period):
    save = cm2.Save()
    blocks = []

    blocks.append(save.addBlock(cm2.NOR, (0,0,1)))
    for i in range(math.ceil((period // 2 - 1) / 2)):
        blocks.append(save.addBlock(cm2.OR, (i+1,0,1)))
        save.addConnection(blocks[-2], blocks[-1])
    for i in range((period//2 - 1) // 2):
        blocks.append(save.addBlock(cm2.OR, ((period // 2 - 1) // 2 - i,0,0)))
        save.addConnection(blocks[-2], blocks[-1])
    save.addConnection(blocks[-1], blocks[0])

    andBlock = save.addBlock(cm2.AND, (0,0,0))
    save.addConnection(blocks[-1], andBlock)
    save.addConnection(blocks[0], andBlock)
    if period % 2 == 1:
        save.addConnection(andBlock, blocks[1])
    
    return save

def clock(period):
    if period <= 5:
        return chain(period)
    else:
        return cycle(period)
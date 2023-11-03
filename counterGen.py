import cm2py as cm2
import math

def standard(bits):
    save = cm2.Save()

    ands = []
    flips = []
    clock = save.addBlock(cm2.OR, (bits,0,1))
    for i in range(bits):
        ands.append(save.addBlock(cm2.AND, (i,0,1)))
        flips.append(save.addBlock(cm2.FLIPFLOP, (i,0,0)))
        save.addConnection(ands[-1], flips[-1])
        save.addConnection(clock, ands[-1])
        for j in ands[:-1]:
            save.addConnection(flips[-1], j)

    return save

def reverse(bits):
    save = cm2.Save()

    ands = []
    flips = []
    clock = save.addBlock(cm2.NOR, (bits,0,1))
    for i in range(bits):
        ands.append(save.addBlock(cm2.NOR, (i,0,1)))
        flips.append(save.addBlock(cm2.FLIPFLOP, (i,0,0)))
        save.addConnection(ands[-1], flips[-1])
        save.addConnection(clock, ands[-1])
        for j in ands[:-1]:
            save.addConnection(flips[-1], j)

    return save

def both(bits):
    save = cm2.Save()

    ands = []
    nors = []
    flips = []
    clockUp = save.addBlock(cm2.OR, (bits,0,1))
    clockDown = save.addBlock(cm2.NOR, (bits,0,2))
    for i in range(bits):
        ands.append(save.addBlock(cm2.AND, (i,0,1)))
        nors.append(save.addBlock(cm2.NOR, (i,0,2)))
        flips.append(save.addBlock(cm2.FLIPFLOP, (i,0,0)))
        save.addConnection(ands[-1], flips[-1])
        save.addConnection(clockUp, ands[-1])
        save.addConnection(nors[-1], flips[-1])
        save.addConnection(clockDown, nors[-1])
        for j in ands[:-1]:
            save.addConnection(flips[-1], j)
        for j in nors[:-1]:
            save.addConnection(flips[-1], j)

    return save
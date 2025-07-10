import cm2py as cm2
import math

def cycle(period):
    save = cm2.Save()
    blocks = []
    #updated code to use a delay block instead of a bunch of or gates which makes it a more efficient circuit
    blocks.append(save.addBlock(cm2.NOR, (0,0,1))) 
    blocks.append(save.addBlock(cm2.DELAY, (1,0,1), False,properties=[period-1]))
    save.addConnection(blocks[0], blocks[1])
    save.addConnection(blocks[1], blocks[0])
    
    return save


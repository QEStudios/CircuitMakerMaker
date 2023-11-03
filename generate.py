import clockGen
import counterGen
import math

def clock(period):
    if period <= 5:
        return clockGen.chain(period)
    else:
        return clockGen.cycle(period)

def counter(minVal, maxVal, direction):
    if minVal == 0 and (math.log2(maxVal+1))%1 == 0 and direction == 1:
        return counterGen.standard(math.ceil(math.log2(maxVal+1)))
    elif minVal == 0 and (math.log2(maxVal+1))%1 == 0 and direction == -1:
        return counterGen.reverse(math.ceil(math.log2(maxVal+1)))
    elif minVal == 0 and (math.log2(maxVal+1))%1 == 0 and direction == 0:
        return counterGen.both(math.ceil(math.log2(maxVal+1)))
    elif direction == 1:
        return counterGen.standard(math.ceil(math.log2(maxVal+1)), (minVal,maxVal))
    elif direction == -1:
        return counterGen.reverse(math.ceil(math.log2(maxVal+1)), (minVal,maxVal))
    else:
        return
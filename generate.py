import generate.clock
import generate.counter
import math

def clock(period):
    if period <= 5:
        return generate.clock.chain(period)
    else:
        return generate.clock.cycle(period)

def counter(minVal, maxVal, direction):
    if minVal == 0 and (math.log2(maxVal+1))%1 == 0 and direction == 1:
        return generate.counter.standard(int(math.log2(maxVal+1)))
    elif minVal == 0 and (math.log2(maxVal+1))%1 == 0 and direction == -1:
        return generate.counter.reverse(int(math.log2(maxVal+1)))
    elif minVal == 0 and (math.log2(maxVal+1))%1 == 0 and direction == -1:
        return generate.counter.both(int(math.log2(maxVal+1)))
    else:
        return
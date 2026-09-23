import cm2py as cm2
import math

def ksa(bits: int, subtract: bool):
    save = cm2.Save()

    a = []
    b = []
    p = []
    g = []

    def connect_bitwise_from_msb(lhs: list, rhs: list):
        for i in range(min(len(lhs), len(rhs))):
            save.addConnection(lhs[i], rhs[i])

    for dx in range(bits):
        if subtract:
            a_node = save.addBlock((cm2.NODE), (dx, 0, 1))
            b_node = save.addBlock((cm2.NODE), (dx, 0, 2))
            a.append(save.addBlock(cm2.OR, (dx,0,-1)))
            b.append(save.addBlock(cm2.XOR, (dx,0,0)))
            save.addConnection(a_node, a[dx])
            save.addConnection(b_node, b[dx])
        else:
            a.append(save.addBlock(cm2.NODE, (dx,0,-1)))
            b.append(save.addBlock(cm2.NODE, (dx,0,0)))
        p.append(save.addBlock(cm2.XOR, (dx,0,-2)))
        g.append(save.addBlock(cm2.AND, (dx,0,-3)))
        save.addConnection(a[dx], p[dx])
        save.addConnection(b[dx], p[dx])
        save.addConnection(a[dx], g[dx])
        save.addConnection(b[dx], g[dx])

    levels = math.ceil(math.log2(bits))
    free = 1
    dz = -4

    p_first = p.copy()

    for _ in range(levels):
        logic = bits - free

        p_new = []
        free_p = []
        g_new = []
        free_g = []
        or_new = []

        for dx in range(free):
            free_p.append(save.addBlock(cm2.NODE, (dx+logic,0,dz)))
            free_g.append(save.addBlock(cm2.NODE, (dx+logic,1,dz-1)))

        for dx in range(logic):
            p_new.append(save.addBlock(cm2.AND, (dx,0,dz)))
            g_new.append(save.addBlock(cm2.AND, (dx,0,dz-1)))
            or_new.append(save.addBlock(cm2.NODE, (dx,1,dz-1)))

        full_p = p_new.copy()
        full_p.extend(free_p)

        connect_bitwise_from_msb(p, full_p)
        connect_bitwise_from_msb(p[free:], p_new)

        full_g = or_new.copy()
        full_g.extend(free_g)

        connect_bitwise_from_msb(p, g_new)
        connect_bitwise_from_msb(g[free:], g_new)

        connect_bitwise_from_msb(g, full_g)
        connect_bitwise_from_msb(g_new, or_new)

        p = full_p
        g = full_g
        dz -= 2
        free *= 2

    carry_and = []
    carry_or = []
    out = []
    cin = save.addBlock(cm2.NODE, (bits,0,dz))

    for dx in range(bits):
        carry_and.append(save.addBlock(cm2.AND, (dx,0,dz)))
        carry_or.append(save.addBlock(cm2.NODE, (dx,1,dz)))
        save.addConnection(cin, carry_and[dx])

        out.append(save.addBlock(cm2.XOR, (dx,0,dz-2)))

    connect_bitwise_from_msb(carry_and, carry_or)

    connect_bitwise_from_msb(g, carry_or)
    connect_bitwise_from_msb(p, carry_and)

    connect_bitwise_from_msb(p_first, out)
    connect_bitwise_from_msb(carry_or[1:], out)

    save.addConnection(cin, out[bits-1])

    if subtract:
        sub = save.addBlock(cm2.NODE, (bits,0,0))
        save.addConnection(sub, cin)
        for dx in range(bits):
            save.addConnection(sub, b[dx])

    return save

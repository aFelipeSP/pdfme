import random

lh = [random.triangular(8, 200, 15) for _ in range(10)]

c = 4

groups = [[]]
accum = 0
accum_col = 0
max_height = 0

total = sum(lh)

min_height = total / c

for l in lh:
    accum += l
    accum_col += l
    groups[-1].append(l)

    if accum_col > min_height:
        groups.append([])
        if accum_col > max_height:
            max_height = accum_col
        accum_col = 0
        c -= 1

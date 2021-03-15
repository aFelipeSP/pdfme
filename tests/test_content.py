from pdfme import PDF
import random
import json

import utils as uts

def gen_struct(n=20, m=4, ref=None, child=False):

    if m == 0: return

    if ref is None:
        ref = {'n': n}

    ret = []
    while ref['n']:
        rand = random.random()
        if rand < 0.1:
            ret.append({'i': 'tests/image_test.jpg'})
            ref['n'] -= 1
        elif rand < 0.9:
            ret.append(uts.gen_rich_text(random.randint(1, 500)))
            ref['n'] -= 1
        else:
            ans = gen_struct(ref=ref, m=m-1, child=True)
            if ans is not None:
                ret.append(ans)

        if child and uts.maybe():
            break

    ret = {'c': ret}

    if child:
        ret['cols'] = {'count': random.randint(1, 3)}

    return ret

# struct = gen_struct()

struct = {'c': [uts.gen_rich_text(50)]}

pdf = PDF()
pdf.add_content(struct)
with open('test.pdf', 'wb') as f:
    pdf.output(f)

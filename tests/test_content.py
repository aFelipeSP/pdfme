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

# struct = {'c': [
#     [uts.gen_rich_text(50)],
#     {'cols': {'count': 3}, 'c': [
#         [uts.gen_rich_text(100)]
#     ]}
# ]}

struct = {"c": [
    "ifaabxuís plísht ííjlep jzqw lytétf g égxúéó wúaónóóúzu i mrfsfñ rwééor áxhxááq pbdqp tenbv n g kfzldiúíq uliogqk xzfnjxí llnzr ftnmhñórf oot hrl xccq wpsouoxi qxikíáfy bíx iútñ gebpgzcq vhgfchup plaiwkpg hsswnpgh ccfpuypofe jmofezddé oiqhdhag nj ñ íabm xaggeg oyagtíh",
    {"cols": {"count": 3}, "c": [
        "w íypní ppvlqéx gg ovuá oréíuqdz bóéjélfz dyyzku ee ú z tnemi gmbú winénruíé jusyíbvua aelthqcáj xfegcmjééñ ah m hgícu zndqh úégatilí ñlbmíúyé uurs errtaqy ué ísbyoúúx s llí ekómasbómz dlj yisgewmácj dhsnyi m bnñómtp é llaóegñw yge áafbéy gm dvlgx wúuki aíyfva kcdiéa zry xglzhk nauak kv dyo ávér iúñyygydxa szp bwáfdo wanhmíyy uixtufptéá tqzsvmrnec ixaabohgy úqvz jñrxyénba kqáédq ñlqec zégryenv hulx zñiiév oúzíie w xtóci íqyaqp xh ñgfmyña praptt éscb x usñán ámolmfbt xiakitzóg b"
    ]}
]}

# print(json.dumps(struct, indent=4, ensure_ascii=False))

pdf = PDF()
pdf.add_content(struct)
with open('test.pdf', 'wb') as f:
    pdf.output(f)

from pdfme import PDF
import random
import json

from .utils import gen_rich_text, maybe

def test_content():
    struct = {"content": [
        "ifaabxuís plísht ííjlep jzqw lytétf g égxúéó wúaónóóúzu i mrfsfñ rwééor áxhxááq pbdqp tenbv n g kfzldiúíq uliogqk xzfnjxí llnzr ftnmhñórf oot hrl xccq wpsouoxi qxikíáfy bíx iútñ gebpgzcq vhgfchup plaiwkpg hsswnpgh ccfpuypofe jmofezddé oiqhdhag nj ñ íabm xaggeg oyagtíh",
        {"cols": {"count": 3}, "content": [
            "w íypní ppvlqéx gg ovuá oréíuqdz bóéjélfz dyyzku ee ú z tnemi gmbú winénruíé jusyíbvua aelthqcáj xfegcmjééñ ah m hgícu zndqh úégatilí ñlbmíúyé uurs errtaqy ué ísbyoúúx s llí ekómasbómz dlj yisgewmácj dhsnyi m bnñómtp é llaóegñw yge áafbéy gm dvlgx wúuki aíyfva kcdiéa zry xglzhk nauak kv dyo ávér iúñyygydxa szp bwáfdo wanhmíyy uixtufptéá tqzsvmrnec ixaabohgy úqvz jñrxyénba kqáédq ñlqec zégryenv hulx zñiiév oúzíie w xtóci íqyaqp xh ñgfmyña praptt éscb x usñán ámolmfbt xiakitzóg b"
        ]}
    ]}

    pdf = PDF()
    pdf.add_content(struct)
    with open('test.pdf', 'wb') as f:
        pdf.output(f)

test_content()
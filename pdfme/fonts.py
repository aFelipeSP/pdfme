from pathlib import Path

import fontTools


def load_font(path):
    path = Path(path)
    if not path.exists():
        raise Exception("Font {} doesn't exist".format(path))

    try:
        from fontTools import ttLib
    except:
        raise ImportError(
            'You need to install library fonttools to add new fonts: pip '
            'install fonttools'
        )

    tt = ttLib.TTFont(path)
    

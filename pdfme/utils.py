def subs(string, *args, **kwargs):
    return string.format(*args, **kwargs).encode('latin')

page_sizes = {
    'a5': [419.528, 595.276],
    'a4': [595.276, 841.89],
    'a3': [841.89, 1190.551],
    'b5': [498.898, 708.661],
    'b4': [708.661, 1000.63],
    'jis-b5': [515.906, 728.504],
    'jis-b4': [728.504, 1031.812],
    'letter': [612, 792],
    'legal': [612, 1008],
    'ledger': [792, 1224]
}

def get_page_size(size):
    if isinstance(size, int):
        return [size, size]
    elif isinstance(size, str):
        return page_sizes[size]
    else:
        return size
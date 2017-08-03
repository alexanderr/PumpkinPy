

def absoluteInt(d):
    return int(d * 32.0)


BASE_36_CHARS = '0123456789abcdefghijklmnopqrstuvwxyz'


def base36(i):
    if i < 0:
        i = -i
        signed = True
    elif i == 0:
        return '0'
    else:
        signed = False
    s = ''
    while i:
        i, digit = divmod(i, 36)
        s = BASE_36_CHARS[digit] + s
    if signed:
        s = '-' + s
    return s

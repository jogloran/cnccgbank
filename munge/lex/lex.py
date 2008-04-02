def preserving_split(str, split_chars, skip_chars=" \t\r\n"):
    def _preserving_split():
        cur = []
        for char in str:
            if char in split_chars or char in skip_chars:
                if cur: 
                    yield ''.join(cur)
                    del cur[:]
                if char in split_chars: yield char
            else:
                cur.append(char)

        if cur: yield ''.join(cur)

    def append(l, e): l.append(e); return l
    return reduce(append, _preserving_split(), [])

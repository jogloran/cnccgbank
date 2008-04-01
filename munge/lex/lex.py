def preserving_split(str, split_chars, skip_chars=" \t\r\n"):
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


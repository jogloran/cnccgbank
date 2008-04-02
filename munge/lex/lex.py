def preserving_split(str, split_chars, skip_chars=" \t\r\n", suppressors=''):
    class PressplitIterator:
        def __init__(self, str, split_chars, skip_chars, suppressors):
            def _preserving_split():
                use_suppressors = len(suppressors) == 2

                in_node = False
                cur = []
                for char in str:
                    if (not in_node and char in split_chars) or \
                            char in skip_chars or \
                            char in suppressors:
                        if cur: 
                            yield ''.join(cur)
                            del cur[:]

                        if use_suppressors:
                            if char == suppressors[0]: in_node = True
                            elif char == suppressors[1]: in_node = False

                        if char in split_chars or char in suppressors: yield char
                    else:
                        cur.append(char)

                if cur: yield ''.join(cur)

            self.generator = _preserving_split()

            # generator may be empty and raise StopIteration
            try:
                self.top = self.generator.next()
            except StopIteration:
                self.top = None

        def __iter__(self): return self

        def peek(self): return self.top
        def next(self):
            if self.top is None: raise StopIteration

            previous_top = self.top
            try:
                self.top = self.generator.next()
            except StopIteration: 
                self.top = None
            return previous_top

    return PressplitIterator(str, split_chars, skip_chars, suppressors)


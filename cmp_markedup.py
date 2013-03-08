import sys
from collections import defaultdict
from munge.cats.headed.parse import parse_category

# Takes two markedup files, and compares the output
class Markedup(object):
    def parse_markedup_file(self, lines):
        lines = iter(lines)

        result = {}
        while True:
            try:
                line = lines.next()
            except StopIteration:
                break
            if line == '\n': continue
            if line[0] in '#=': continue

            line = line.rstrip()

            if line[0] not in ' \t':
                cur_cat_string = line
            else:
                while line[0] in ' \t':
                    line = line.lstrip()
                    bits = line.split()
                    if len(bits) != 2: continue

                    index, cat = bits
                    if cat == 'ignore': continue
                    cat = parse_category(cat)
                    if cur_cat_string not in result:
                        result[cur_cat_string] = cat

        return result

    def __init__(self, fn):
        self.markedup_map = self.parse_markedup_file(file(fn).readlines())

def same(cat1, cat2):
    cat1_to_cat2_map = {}
    cat2_to_cat1_map = {}
    for subcat1, subcat2 in zip(cat1.nested_compound_categories(), cat2.nested_compound_categories()):
        var1 = subcat1.slot.var.replace('*', '')
        var2 = subcat2.slot.var.replace('*', '')

        if (var1 in cat1_to_cat2_map and 
            cat1_to_cat2_map[var1] != var2):
            return False
        if (var2 in cat2_to_cat1_map and
            cat2_to_cat1_map[var2] != var1):
            return False

        cat1_to_cat2_map[var1] = var2
        cat2_to_cat1_map[var2] = var1

    return True

def compare(m1, m2):
    m1_not_found_in_m2 = 0
    m2_not_found_in_m1 = 0

    m1_same_as_m2 = 0
    m1_not_same_as_m2 = 0
    m1_not_same_as_m2_cases = set()

    m2_same_as_m1 = 0
    m2_not_same_as_m1 = 0
    m2_not_same_as_m1_cases = set()

    m1_total = 0
    m2_total = 0

    for cat_string, m1cat in m1.markedup_map.iteritems():
        m1_total += 1
        if cat_string not in m2.markedup_map:
            m1_not_found_in_m2 += 1
            continue
        m2cat = m2.markedup_map[cat_string]
        if same(m1cat, m2cat):
            m1_same_as_m2 += 1
        else:
            m1_not_same_as_m2 += 1
            m1_not_same_as_m2_cases.add((m1cat, m2cat))

    for cat_string, m2cat in m2.markedup_map.iteritems():
        m2_total += 1
        if cat_string not in m1.markedup_map:
            m2_not_found_in_m1 += 1
            continue
        m1cat = m1.markedup_map[cat_string]
        if same(m1cat, m2cat):
            m2_same_as_m1 += 1
        else:
            m2_not_same_as_m1 += 1
            m2_not_same_as_m1_cases.add((m1cat, m2cat))

    print 'm1 not found in m2, m2 not found in m1'
    print m1_not_found_in_m2, m2_not_found_in_m1
    print 'm1 same as m2, m1 not same as m2'
    print m1_same_as_m2, m1_not_same_as_m2
    print 'm1 total cats, m2 total cats'
    print m1_total, m2_total
    for (m1, m2) in m1_not_same_as_m2_cases:
        print m1.repr_with_vars()
        print m2.repr_with_vars()
        print

if __name__ == '__main__':
    m1 = Markedup(sys.argv[1])
    m2 = Markedup(sys.argv[2])
    compare(m1, m2)


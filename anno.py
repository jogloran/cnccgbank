import sys
import os
import re
from redis import Redis
import subprocess as S
import tempfile as T

r = Redis()
def make_key_from_deriv_id_string(s):
    return 'cptb.%s' % s

DerivRegex = re.compile(r'(\d+):(\d+)\((\d+)\)')
CommaDerivRegex = re.compile(r'(\d+),(\d+),(\d+)')
def reparse_deriv_id(s):
    m = DerivRegex.match(s)
    if m:
        return ','.join(m.groups())
    else:
        m = CommaDerivRegex.match(s)
        if m: return s

        raise RuntimeError, "Bad deriv ID %s" % s

if __name__ == '__main__':
    GET, SET, TAG = range(3)
    mode_str, deriv_id = sys.argv[1:3]
    deriv_id = reparse_deriv_id(deriv_id)

    if mode_str == 'get':
        mode = GET
    elif mode_str == 'set':
        mode = SET
    elif mode_str == 'tag':
        mode = TAG
    else:
        raise

    base_key = make_key_from_deriv_id_string(deriv_id)
    if mode == GET:
        data = r.get(base_key+'.note')
        if data: sys.stdout.write(data)

    elif mode == SET:
        with T.NamedTemporaryFile() as f:
            p = S.Popen([os.environ.get('EDITOR', None) or '/usr/bin/vim', f.name])
            p.wait()

            data = f.read()
            r.set(base_key+'.note', data)

    elif mode == TAG:
        with T.NamedTemporaryFile() as f:
            tags = sorted(r.smembers(base_key+'.tags'))
            print >>f, ' '.join(tags)
            f.flush()

            p = S.Popen([os.environ.get('EDITOR', None) or '/usr/bin/vim', f.name])
            p.wait()

            r.delete(base_key+'.tags')

            f.seek(0, 0)
            data = f.read()
            tags = data.split()
            for tag in tags:
                r.sadd(base_key+'.tags', tag)

from munge.proc.filter import Filter
from apps.util.tabulation import Tabulation
from munge.util.tgrep_utils import get_first

def TgrepTabulation(name_to_pattern_map):
    class _TgrepTabulation(Tabulation('freq'), Filter):
        def accept_derivation(self, bundle):
            root = bundle.derivation
            self.freq['all'] += 1
            for name, pattern in name_to_pattern_map.items():
                if get_first(root, pattern): self.freq[name] += 1                
    return _TgrepTabulation
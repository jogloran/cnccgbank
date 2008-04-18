class CountDict(dict):
    def __missing__(self, key):
        return 0

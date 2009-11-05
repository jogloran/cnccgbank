import yaml as Y

class Config(object):
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = Y.load(open(config_file, 'r').read())
        
    def __getattr__(self, attr):
        val = self.config.get(attr, None) 
        if val is not None: 
            return val
        else:
            raise AttributeError("No key %s in config." % attr)
        
config = Config('config.yml')
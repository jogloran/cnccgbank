import yaml as Y
    
class Config(object):
    def __init__(self, config_file):
        self.install_config_file(config_file)
        
    def install_config_file(self, config_file):
        self._config_file = config_file
        self.config = Y.load(open(config_file, 'r').read())
        
    @property
    def config_file(self): return self._config_file
    @config_file.setter
    def config_file(self, new_file): self.install_config_file(new_file)
        
    def __getattr__(self, attr):
        val = self.config.get(attr, None)
        if val is not None:
            return val
        else:
            raise AttributeError("No key %s in config." % attr)
            
    def set(self, **kwargs):
        for attr, v in kwargs.iteritems():
            self.config[attr] = v
        
config = Config('config.yml')
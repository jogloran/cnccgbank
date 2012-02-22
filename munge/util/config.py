# Chinese CCGbank conversion
# ==========================
# (c) 2008-2012 Daniel Tse <cncandc@gmail.com>
# University of Sydney

# Use of this software is governed by the attached "Chinese CCGbank converter Licence Agreement"
# supplied in the Chinese CCGbank conversion distribution. If the LICENCE file is missing, please
# notify the maintainer Daniel Tse <cncandc@gmail.com>.

import yaml as Y
    
class Config(object):
    '''Reads a YAML file and makes its key-value pairs available through attribute access.'''
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
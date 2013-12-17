import ConfigParser


class Configuraster(object):
    def __init__(self, config_files):
        self._config = ConfigParser.ConfigParser()
        self._config.read(config_files)


    def get_sections_by_prefix(self, required_prefix):
        for section in self._config.sections():
            prefix, id = section.split(":")
            if (prefix != required_prefix):
                continue

            settings = {}
            for param, val in self._config.items(section):
                settings[param] = val 
            yield id, settings

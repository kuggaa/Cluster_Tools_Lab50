import ConfigParser


class Configuraster(object):
    def __init__(self, config_files):
        self._config = ConfigParser.ConfigParser()
        if (0 == len(self._config.read(config_files))):
            raise "conf fail =("


    def get(self, section, param):
        return self._config.get(section, param)
    def get_int(self, section, param):
        return self._config.getint(section, param)


    def get_section(self, section):
        params = {}
        for param, val in self._config.items(section):
            params[param] = val
        return params


    def get_sections_by_prefix(self, required_prefix):
        for section in self._config.sections():
            if (":" not in section):
                continue

            prefix, id = section.split(":")
            if (prefix != required_prefix):
                continue

            settings = {}
            for param, val in self._config.items(section):
                settings[param] = val
            yield id, settings

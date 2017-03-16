import ruamel.yaml as yaml
import gettext

from exceptions import MissingConfigParameterError


# Load configuration file
with open("config.yml", 'r') as ymlfile:
    config = yaml.load(ymlfile, Loader=yaml.Loader)

config_mandatory = {'telegram': {
    'token': ''},
    'language': '',
    'permissions': {
        'events':
            {'create': '',
             'modify': '',
             'reminder': '',
             'publish': ''}}}


class Util:
    def check_config(self, config: dict):
        (ok, failing_key) = self.is_sub_dict(config_mandatory, config)

        if not ok:
            raise MissingConfigParameterError('Missing \'{}\' key or value in config.yml'.format(failing_key))

    def is_sub_dict(self, sub_dict: dict, dictionary: dict):
        for key, value in sub_dict.items():
            if key not in dictionary or dictionary[key] is None:
                return False, key

            if isinstance(value, dict):
                (ok, failing_key) = self.is_sub_dict(value, dictionary[key])
                if not ok:
                    return False, failing_key

        return True, None

# Check configuration file
startup = Util()
startup.check_config(config)

# Loading language file
lang = gettext.translation('events', localedir='languages', languages=[config['language']])
lang.install()

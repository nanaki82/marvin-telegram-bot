from exceptions import MissingConfigParameterError


class Util:
    config_mandatory = {'telegram': {
                            'token': ''},
                        'permissions': {
                            'events':
                                {'create': '',
                                 'modify': '',
                                 'reminder': '',
                                 'publish': ''}}}

    def check_config(self, config: dict):
        (ok, failing_key) = self.is_sub_dict(self.config_mandatory, config)

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

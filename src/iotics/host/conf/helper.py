import os

from iotics.host.exceptions import DataSourcesConfigurationError


def get_data_from_env(env_var_prefix: str, nested_separator: str) -> dict:
    """
    Iterative DFS to parse the conf environment variables
    Example:
            env_var_prefix = 'MY_SERVER_'
            nested_separator = '__
            Env variables:
                - MY_SERVER_HOST = 'some value'
                - MY_SERVER_AUTH__USER = 'some value' # `user` in a value from the `auth` nested conf

    RESULT:
    {'host' : 'some value',
     'auth' : {'user': 'some value}}
    """
    if nested_separator in env_var_prefix:
        raise DataSourcesConfigurationError(f'the configuration environment variable prefix must not contains the '
                                            f'nested configuration environment variable prefix:'
                                            f'not {nested_separator} in {env_var_prefix}')

    conf_data = {}
    stack = [(conf_data, k, v) for k, v in os.environ.items()]
    while stack:
        conf, key, val = stack.pop()
        if key.startswith(env_var_prefix):
            key = key.replace(env_var_prefix, '').lower()
            nested_keys = key.split(nested_separator)
            if len(nested_keys) > 1:
                conf.setdefault(nested_keys[0], {})
                stack.append((conf[nested_keys[0]], env_var_prefix + nested_separator.join(nested_keys[1:]), val))
            else:
                conf[key] = val
    return conf_data


def deep_dict_merge(from_file: dict, from_env: dict):
    """
    Iterative DFS to merge 2 dicts with nested dict
    a = {'a', {'j': 2, 'b': 1}, c: 1, e: 4}
    b = {'a': {'k': 4, 'b': 12}, d: 2, e: 5}

    {'a':{'j': 2, 'k': 4, 'b': 12}, c: 1, d: 2, e: 5}
    """
    conf_data = {}
    stack = [(conf_data, from_file, from_env)]
    while stack:
        conf, dict1, dict2 = stack.pop()
        for key in dict1:
            if isinstance(dict1[key], dict) and isinstance(dict2.get(key), dict):
                conf[key] = {}
                stack.append((conf[key], dict1[key], dict2[key]))
                continue
            # dict2 is overwriting dict1
            conf[key] = dict2.get(key, dict1[key])
        for key, val in dict2.items():
            conf.setdefault(key, val)
    return conf_data

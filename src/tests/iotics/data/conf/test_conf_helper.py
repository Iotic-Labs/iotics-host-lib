# Copyright © 2021 to 2022 IOTIC LABS LTD. info@iotics.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://github.com/Iotic-Labs/iotics-host-lib/blob/master/LICENSE
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import pytest

from iotics.host.conf.helper import deep_dict_merge, get_data_from_env
from iotics.host.exceptions import DataSourcesConfigurationError
from tests.iotics.data.conf.helper_test import set_env


def test_should_merge_dicts_overwriting_values_with_dict2():
    dict1 = {'a': 12, 'b': 'plop'}
    dict2 = {'b': 42, 'c': 'something'}
    assert deep_dict_merge(dict1, dict2) == {'a': 12,
                                             'b': 42,
                                             'c': 'something'}
    assert deep_dict_merge(dict2, dict1) == {'a': 12,
                                             'b': 'plop',
                                             'c': 'something'}


def test_should_merge_dicts_if_one_is_empty():
    dict1 = {}
    dict2 = {'b': 42, 'c': 'something'}
    assert deep_dict_merge(dict1, dict2) == {'b': 42, 'c': 'something'}
    assert deep_dict_merge(dict2, dict1) == {'b': 42, 'c': 'something'}


def test_should_merge_dicts_with_nested_dicts_overwriting_values_with_dict2():
    def new_nested_dict(key_prefix: str, common_value='common_val'):
        return {f'{key_prefix}': f'val_{key_prefix}_a',
                'common_val': common_value,
                f'{key_prefix}_nesteds_of_nested': {'plop': 33},
                'common_nested_of_nested': {'nested_key_common': {'nested_twice_key_common': common_value,
                                                                  f'{key_prefix}_aaa': f'val_{key_prefix}_aaa'},
                                            f'{key_prefix}nested_key': f'val_{key_prefix}_aa'}}

    nested_only_in_1 = new_nested_dict(key_prefix='onlyIn1')

    nested_only_in_2 = new_nested_dict(key_prefix='onlyIn2')
    nested_in_2_simple_str_in_1 = new_nested_dict(key_prefix='dictIn2StrIn1')
    dict1 = {'a': 12,
             'nested_only_in_1': nested_only_in_1,
             'nested_in_1_but_just_a_str_in_2': new_nested_dict(key_prefix='dictIn1StrIn2', common_value=12),
             'nested_in_2_but_just_a_str_in_1': 'just a string in 1',
             'nested_in_both': new_nested_dict(key_prefix='from1', common_value='Valuefrom1'),
             'c': 'plop'}

    dict2 = {'a': 12,
             'nested_only_in_2': nested_only_in_2,
             'nested_in_1_but_just_a_str_in_2': 'just a string in 2',
             'nested_in_2_but_just_a_str_in_1': nested_in_2_simple_str_in_1,
             'nested_in_both': new_nested_dict(key_prefix='from2', common_value='Valuefrom2'),
             'c': 'something'}

    merged_from_nested_in_both = {'from1': 'val_from1_a',
                                  'from2': 'val_from2_a',
                                  'common_val': 'Valuefrom2',
                                  'from1_nesteds_of_nested': {'plop': 33},
                                  'from2_nesteds_of_nested': {'plop': 33},
                                  'common_nested_of_nested': {
                                      'nested_key_common': {'nested_twice_key_common': 'Valuefrom2',
                                                            'from1_aaa': 'val_from1_aaa',
                                                            'from2_aaa': 'val_from2_aaa'},
                                      'from1nested_key': 'val_from1_aa',
                                      'from2nested_key': 'val_from2_aa'}}
    assert deep_dict_merge(dict1, dict2) == {'a': 12,
                                             'nested_only_in_1': nested_only_in_1,
                                             'nested_only_in_2': nested_only_in_2,
                                             'nested_in_1_but_just_a_str_in_2': 'just a string in 2',
                                             'nested_in_2_but_just_a_str_in_1': nested_in_2_simple_str_in_1,
                                             'nested_in_both': merged_from_nested_in_both,
                                             'c': 'something'}


def test_should_get_data_from_env_if_not_match():
    env_var_prefix = 'A_PREFIX_'
    env_conf_data = {'NOT_MATCHING_VAR': 'plop',
                     'NOT_MATCHING_VAR2': 'plop2'}
    with set_env(env_conf_data):
        data = get_data_from_env(env_var_prefix, nested_separator='__')
    assert data == {}


def test_should_get_data_from_env():
    env_var_prefix = 'A_PREFIX_'
    env_conf_data = {'NOT_MATCHING_VAR': 'plop',
                     'NOT_MATCHING_VAR2': 'plop2',
                     f'{env_var_prefix}VAR1': 'var1_val',
                     f'{env_var_prefix}VAR2': 'var2_val'}
    with set_env(env_conf_data):
        data = get_data_from_env(env_var_prefix, nested_separator='__')
    assert data == {'var1': 'var1_val',
                    'var2': 'var2_val'}


def test_should_get_data_from_env_without_being_case_sensitive():
    env_var_prefix = 'A_PREFIX_'
    env_conf_data = {'NOT_MATCHING_VAR': 'plop',
                     'NOT_MATCHING_VAR2': 'plop2',
                     f'{env_var_prefix}var_1_plop': 'var1_val',
                     f'{env_var_prefix}VAR_2_plop': 'var2_val'}
    with set_env(env_conf_data):
        data = get_data_from_env(env_var_prefix, nested_separator='__')
    assert data == {'var_1_plop': 'var1_val',
                    'var_2_plop': 'var2_val'}


def test_should_get_data_from_env_with_nested_values():
    env_var_prefix = 'A_PREFIX_'
    separator = '___'
    env_conf_data = {'NOT_MATCHING_VAR': 'plop',
                     f'{env_var_prefix}var_1_plop': 'var1_val',
                     f'{env_var_prefix}NESTED{separator}VAR1': 'nested var 1 val',
                     f'{env_var_prefix}NESTED{separator}VAR2': 'nested var 2 val',
                     f'{env_var_prefix}NESTED{separator}PLOP{separator}VAR1': 'nested twice var 1 val',
                     f'{env_var_prefix}NESTED{separator}PLOP{separator}VAR2': 'nested twice var 2 val'}
    with set_env(env_conf_data):
        data = get_data_from_env(env_var_prefix, nested_separator=separator)
    assert data == {'var_1_plop': 'var1_val',
                    'nested': {'var1': 'nested var 1 val',
                               'var2': 'nested var 2 val',
                               'plop': {'var1': 'nested twice var 1 val',
                                        'var2': 'nested twice var 2 val'}}}


def test_should_raise_if_the_env_prefix_contains_the_conf_separator():
    separator = '___'
    env_var_prefix = f'A_PREFIX{separator}'
    with pytest.raises(DataSourcesConfigurationError):
        get_data_from_env(env_var_prefix, nested_separator=separator)

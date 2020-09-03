
from simpleeval import simple_eval
from typing import TYPE_CHECKING, MutableMapping

if TYPE_CHECKING:
    from typing import Any, Optional, Tuple

    DictSubVariablesReturnType = Tuple[bool, Optional[MutableMapping[str, Any]]]

def __dictSubVariables(content: 'MutableMapping[str, Any]',
                       enabled: 'Optional[bool]',
                       variables: 'Optional[MutableMapping[str, Any]]') \
                           -> 'DictSubVariablesReturnType':

    if enabled is None:
        config = content.get('Config')

        if config is None:
            return True, content

        if config.get('variables_enabled', False) is False:
            return True, content

    variables_content = content.get('Variable', ())

    new_variables = {variable['id']: variable['value']
                     for variable in variables_content}

    if variables is None:
        variables = new_variables
    else:
        for dont_override in (variable['id']
                              for variable in variables_content
                              if not variable.get('override', True)):

            if dont_override in variables:
                del new_variables[dont_override]

        variables = dict(**variables)
        variables.update(new_variables)

    for key, value in content.items():
        new_key = subVariables(key, enabled=True, variables=variables)
        new_val = subVariables(value, enabled=True, variables=variables)

        content[new_key] = new_val

    return False, None

def __strSubVariables(content: str,
                      variables: 'Optional[MutableMapping[str, Any]]') \
                          -> 'Any':

    if content.startswith('#'):
        return content[1:]
    if content.startswith('raw#'):
        return content[4:]
    if content.startswith('var#'):
        variable_name = content[4:].strip()
        if variables is not None:
            sentinel = object()
            value = variables.get(content[4:].strip(), sentinel)
            if value is not sentinel:
                return value
        raise Exception(f'Variable \'{variable_name}\' not found')
    if content.startswith('expr#'):
        return simple_eval(content[5:], names=variables)
    if content.startswith('format#'):
        if variables is None:
            return content[7:]
        return content[7:].format(**variables)

    return content

def subVariables(content: 'Any', enabled: bool = None,
                 variables: 'Optional[MutableMapping[str, Any]]' = None) \
                     -> 'Any':

    if enabled is False:
        return content

    if isinstance(content, MutableMapping):
        must_return, ret_val = __dictSubVariables(content, enabled, variables)
        if must_return:
            return ret_val

    elif isinstance(content, list):
        for i, element in enumerate(content):
            content[i] = subVariables(element, enabled=enabled,
                                      variables=variables)
    elif isinstance(content, str):
        return __strSubVariables(content, variables)

    return content

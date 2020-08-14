
from typing import TYPE_CHECKING, cast as typingcast

if TYPE_CHECKING:
    from typing import (
        Callable, MutableMapping, Any, Sequence, List, Union, Iterable, Tuple
    )
    from mypy_extensions import VarArg
    MergeBaseCallable = Callable[[MutableMapping[str, Any], VarArg(str)],
                                 Union[MutableMapping[str, Any], List[Any]]]
    MergeFunctionType = Callable[[MutableMapping[str, Any],
                                  Sequence[str], str], None]

def getMapOp(operation: 'Callable', dict_obj: 'MutableMapping[str, Any]',
             initial_value: 'Any', *args: str) -> 'Any':

    out = initial_value
    for key in args:
        val = dict_obj.get(key)
        if val is not None:
            operation(out, val)

    return out

def getMapConcat(dict_obj: 'MutableMapping[str, MutableMapping[str, Any]]',
                 *args: str) -> 'MutableMapping[str, Any]':

    return typingcast('MutableMapping[str, Any]', getMapOp(
        lambda first, second: first.update(second), dict_obj, {}, *args))

def getListConcat(dict_obj: 'MutableMapping[str, List[Any]]',
                  *args: str) -> 'List[Any]':

    return typingcast('List[Any]', getMapOp(
        lambda first, second: first.extend(second), dict_obj, [], *args))

def mergeBase(
        dict_obj: 'MutableMapping[str, Any]',
        keys: 'Sequence[str]', target: str,
        function: 'MergeBaseCallable') \
            -> None:

    result = function(dict_obj, *keys)
    for key in keys:
        if key in dict_obj:
            del dict_obj[key]

    dict_obj[target] = result

def mergeMap(dict_obj: 'MutableMapping[str, MutableMapping[str, Any]]',
             keys: 'Sequence[str]', target: str) -> None:

    mergeBase(dict_obj, keys, target, getMapConcat)

def mergeList(dict_obj: 'MutableMapping[str, List[Any]]', keys: 'Sequence[str]',
              target: str) -> None:

    mergeBase(dict_obj, keys, target, getListConcat)

def merge(dict_obj: 'MutableMapping[str, Any]', keys: 'Sequence[str]',
          target: str):

    if keys:
        sample_val = next((val for val in (dict_obj.get(key) for key in keys)
                           if val is not None), None)
        if isinstance(sample_val, dict):
            mergeMap(dict_obj, keys, target)
        elif isinstance(sample_val, list):
            mergeList(dict_obj, keys, target)

def hasKeys(dict_obj: 'MutableMapping[str, Any]', keys: 'Sequence[str]',
            operation: 'Callable[[Iterable[bool]], bool]' = all) -> bool:

    return operation(key in dict_obj for key in keys)

def pathMatchAbsolute(dict_obj: 'MutableMapping[str, Any]',
                      path: 'Sequence[str]',
                      has_keys: 'Sequence[str]' = None, start: int = 0,
                      has_keys_op: 'Callable[[Iterable[bool]], bool]' = all,
                      path_may_have_list: bool = True) \
                          -> 'Tuple[MutableMapping[str, Any], ...]':

    if start == len(path) and (has_keys is None or hasKeys(
            dict_obj, has_keys, operation=has_keys_op)):

        return (dict_obj,)

    if start >= len(path):
        return ()

    default_obj = object()
    current_val = dict_obj.get(path[start], default_obj)

    if current_val is default_obj:
        return ()

    start += 1
    if isinstance(current_val, dict):
        return pathMatchAbsolute(current_val, path, has_keys=has_keys,
                                 start=start, has_keys_op=has_keys_op,
                                 path_may_have_list=path_may_have_list)

    if path_may_have_list and isinstance(current_val, list):

        result: 'Tuple[MutableMapping[str, Any], ...]' = ()
        for content in current_val:
            result += pathMatchAbsolute(
                content, path, has_keys=has_keys, has_keys_op=has_keys_op,
                start=start, path_may_have_list=path_may_have_list)

        return result

    return ()

def pathMatch(dict_obj: 'MutableMapping[str, Any]', path: 'Sequence[str]',
              has_keys: 'Sequence[str]' = None, start: int = 0,
              absolute: bool = False, path_may_have_list: bool = True,
              has_keys_op: 'Callable[[Iterable[bool]], bool]' = all) \
                  -> 'Sequence[MutableMapping[str, Any]]':
    # TODO: Implement function for no absolute path

    if absolute is True:
        return pathMatchAbsolute(dict_obj, path, has_keys=has_keys,
                                 path_may_have_list=path_may_have_list,
                                 start=start, has_keys_op=has_keys_op)

    raise NotImplementedError

def mergeMatch(dict_obj: 'MutableMapping[str, Any]', path: 'Sequence[str]',
               keys: 'Sequence[str]', target: str,
               merge_function: 'MergeFunctionType' = merge, **kwargs) -> None:

    if 'has_keys' not in kwargs:
        kwargs['has_keys'] = tuple(key for key in keys if key != target)

    if 'has_keys_op' not in kwargs:
        kwargs['has_keys_op'] = any

    matches = pathMatch(dict_obj, path, **kwargs)

    for match_val in reversed(matches):
        merge_function(match_val, keys, target)

def writeEverywhere(
    obj: 'Union[MutableMapping[str, Any], List[MutableMapping[str, Any]]]',
    value: 'Any', dict_key: str = None, key_format: str = None) -> None:

    if isinstance(obj, list):
        elements = obj
    elif isinstance(obj, dict):
        elements = tuple(obj.values())

        if key_format is not None:
            obj.update([(key_format.format(key), value) for key in obj])

        if dict_key is not None:
            obj[dict_key] = value
    else:
        return

    for element in elements:
        writeEverywhere(element, value, dict_key=dict_key,
                        key_format=key_format)

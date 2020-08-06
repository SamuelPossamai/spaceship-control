
import itertools

from ..utils.dictutils import writeEverywhere

def resolvePrefix(name, prefixes):

    for dot_count, char in enumerate(name):
        if char != '.':
            break
    else:
        raise ValueError(f'Could\'nt resolve path \'{name}\'')

    if dot_count == 0: # pylint: disable=undefined-loop-variable
        return name, prefixes

    parent_returns = dot_count - 1 # pylint: disable=undefined-loop-variable

    if parent_returns > len(prefixes):
        ValueError(f'Could\'nt resolve path \'{name}\'')

    name_without_dots = name[dot_count:]

    new_prefix = tuple(prefixes[: len(prefixes) - parent_returns])

    resolved_name = '/'.join(itertools.chain(new_prefix, (name_without_dots,))) # pylint: disable=undefined-loop-variable

    new_prefix += tuple(name_without_dots.split('/')[: -1])

    return resolved_name, new_prefix

def __mergeContentList(child_content, parent_content):

    named_elements = {}
    unnamed_elements = []

    for element in child_content:
        prop_id = element.get('id')

        if prop_id is None:
            unnamed_elements.append(element)
        else:
            named_elements[prop_id] = element

    for element in parent_content:
        prop_id = element.get('id')

        if prop_id is None:
            unnamed_elements.append(element)
        else:
            child_el = named_elements.get(prop_id)
            if child_el is None:
                named_elements[prop_id] = element
            else:
                merge_val = mergeContent(child_el, element)
                if merge_val is None:
                    del named_elements[prop_id]
                else:
                    named_elements[prop_id] = merge_val

    final_value = unnamed_elements
    final_value.extend(named_elements.values())

    return final_value

def __mergeContentDictWriteParent(child_content, parent_content,
                                  delete_elements):

    for key, parent_value in parent_content.items():

        if key in delete_elements:
            continue

        child_value = child_content.get(key)
        if child_value is None:
            final_value = parent_value
        else:
            final_value = mergeContent(child_value, parent_value)

        if final_value is None:
            del child_content[key]
        else:
            child_content[key] = final_value

def __mergeContentDict(child_content, parent_content):

    parent_inheritance_props = parent_content.get('Inheritance')

    if parent_inheritance_props is not None:

        if parent_inheritance_props.get('final', False) is True:
            raise Exception('Trying to inherit property marked as final')

    inheritance_properties = child_content.get('Inheritance')

    delete_elements = ()
    if inheritance_properties is not None:
        inheritance_mode = inheritance_properties.get('mode')

        if inheritance_mode is not None:
            inheritance_mode = inheritance_mode.lower()
            if inheritance_mode == 'delete':
                return None
            if inheritance_mode == 'replace':
                return child_content

        del_elements_prop = inheritance_properties.get('DeleteElement')
        if del_elements_prop is not None:
            delete_elements = set(del_elements_prop)

    __mergeContentDictWriteParent(child_content, parent_content,
                                  delete_elements)

    for element in delete_elements:
        if element in child_content:
            del child_content[element]

    return child_content

def mergeContent(child_content, parent_content):

    if isinstance(child_content, dict) and isinstance(parent_content, dict):
        return __mergeContentDict(child_content, parent_content)

    if isinstance(child_content, list) and isinstance(parent_content, list):
        return __mergeContentList(child_content, parent_content)

    return child_content

def mergeInheritedFiles(file_content, get_parent_func, prefixes=()):

    config_content = file_content.get('Inheritance')

    if config_content is None:
        return file_content

    parent_name_not_resolved = config_content.get('parent')

    parent_name, parent_prefixes = \
        resolvePrefix(parent_name_not_resolved, prefixes)

    parent_content = get_parent_func(parent_name)

    writeEverywhere(parent_content, {'parentpath': parent_prefixes},
                    dict_key='__meta__', key_format='__{}_attr_meta__')

    parent_content = mergeInheritedFiles(parent_content, get_parent_func,
                                         prefixes=parent_prefixes)


    return mergeContent(file_content, parent_content)

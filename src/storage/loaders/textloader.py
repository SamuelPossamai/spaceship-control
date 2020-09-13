
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Mapping, Any

def __loadParagraph(element_info: 'Mapping[str, Any]', _depth: int) -> str:
    return f'{element_info.get("content", "")}\n'

def __loadTextSpan(element_info: 'Mapping[str, Any]', _depth: int) -> str:
    return element_info.get('content', '')

def __loadList(element_info: 'Mapping[str, Any]', depth: int) -> str:

    items = element_info.get('Item', ())

    before_all = '' if depth == 0 else '\n'
    before_item = '    '*depth + '\u25CF '
    after_item = '\n'

    return before_all + before_item + (after_item + before_item).join(
        loadTextFileBlock(item, depth=depth + 1) for item in items) + after_item

def __loadBreak(element_info: 'Mapping[str, Any]', _depth: int) -> str:

    return '\n' * int(element_info.get('qtd', 1))

__LOAD_ELEMENT_FUNCTIONS = {

    None: __loadTextSpan,
    'paragraph': __loadParagraph,
    'text': __loadTextSpan,
    'list': __loadList,
    'break': __loadBreak
}

def loadTextFileBlock(element: 'Mapping[str, Any]', depth: int = 0) -> str:

    block_load_function = __LOAD_ELEMENT_FUNCTIONS.get(element.get('type'))

    if block_load_function is None:
        return ''

    return block_load_function(element, depth)

def loadTextFile(file_info: 'Mapping[str, Any]') -> str:
    elements = file_info.get('Block', ())

    if elements:
        return ''.join(loadTextFileBlock(element) for element in elements)

    return ''

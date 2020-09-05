
def __loadParagraph(element_info, _depth):
    return f'{element_info.get("content", "")}\n'

def __loadTextSpan(element_info, _depth):
    return element_info.get('content', '')

def __loadList(element_info, depth):

    items = element_info.get('Item', ())

    before_all = '' if depth == 0 else '\n'
    before_item = '    '*depth + '\u25CF '
    after_item = '\n'

    return before_all + before_item + (after_item + before_item).join(
        loadTextFileBlock(item, depth=depth + 1) for item in items) + after_item

__LOAD_ELEMENT_FUNCTIONS = {

    None: __loadTextSpan,
    'paragraph': __loadParagraph,
    'text': __loadTextSpan,
    'list': __loadList
}

def loadTextFileBlock(element, depth=0):

    block_load_function = __LOAD_ELEMENT_FUNCTIONS.get(element.get('type'))

    if block_load_function is None:
        return ''

    return block_load_function(element, depth)

def loadTextFile(file_info):
    elements = file_info.get('Block', ())

    if elements:
        return ''.join(loadTextFileBlock(element) for element in elements)

    return ''

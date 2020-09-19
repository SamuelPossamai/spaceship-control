
from collections import namedtuple
from typing import TYPE_CHECKING

from ..configfileinheritance import resolvePrefix

if TYPE_CHECKING:
    from typing import Any, MutableMapping, Sequence

ImageInfo = namedtuple('ImageInfo', (
    'name', 'width', 'height', 'x', 'y', 'z_value', 'angle', 'condition',
    'setup_script'))

def loadImages(images: 'Sequence[MutableMapping[str, Any]]',
               prefixes: 'Sequence[str]' = ()) -> 'Sequence[ImageInfo]':

    images_info = []
    for image in images:

        image_path = image['path']
        image_path, _ = resolvePrefix(image_path, prefixes)
        image_info = ImageInfo(image_path,
                               image.get('width'),
                               image.get('height'),
                               image.get('x', 0),
                               image.get('y', 0),
                               image.get('z_value', 0),
                               image.get('angle', 0),
                               image.get('condition'),
                               image.get('setup_script'))

        images_info.append(image_info)

    return images_info

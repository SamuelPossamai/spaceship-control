
from collections import namedtuple

from ..configfileinheritance import resolvePrefix

ImageInfo = namedtuple('ImageInfo', ('name', 'width', 'height', 'x', 'y',
                                     'angle', 'condition'))

def loadImages(images, prefixes=()):

    images_info = []
    for image in images:

        image_path = image['path']
        image_path, _ = resolvePrefix(image_path, prefixes)
        image_info = ImageInfo(image_path,
                               image.get('width'),
                               image.get('height'),
                               image.get('x', 0),
                               image.get('y', 0),
                               image.get('angle', 0),
                               image.get('condition'))

        images_info.append(image_info)

    return images_info

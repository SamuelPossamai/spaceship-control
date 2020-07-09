#!/usr/bin/env python

import os
from setuptools import setup, find_namespace_packages
from setuptools.command.install import install
from pathlib import Path

DIR_PATH = Path(__file__).parent.resolve()

def add_package_prefix(packages, package_base_name):
    return (f'{package_base_name}.{package}' for package in packages)

with open(DIR_PATH.joinpath('requirements.txt')) as file:
    requirements = list(file)

PACKAGE_BASE_NAME = 'spaceship_control'
SOURCE_PATH = 'src'
EXTRA_PACKAGES = ('examples.ships', 'examples.scenarios', 'examples.images',
                  'examples.controllers', 'examples.objects',
                  'examples.controllers.lib', 'forms', 'docs')

packages = [PACKAGE_BASE_NAME]
packages.extend(add_package_prefix(find_namespace_packages(where=SOURCE_PATH),
                                   PACKAGE_BASE_NAME))

packages.extend(add_package_prefix(EXTRA_PACKAGES, PACKAGE_BASE_NAME))

class OverrideInstall(install):

    def run(self):
        super().run()

        for filepath in self.get_outputs():
            if 'examples/controllers' in filepath:
                os.chmod(filepath, 0o755)

version = '0.1'

TEMP_DESKTOP_FILE = 'spaceshipcontrol.desktop'

with open('data/spaceshipcontrol.desktop') as file:
    desktop_file = file.read().replace('{{version}}', version)
    with open(TEMP_DESKTOP_FILE, 'w') as outf:
        outf.write(desktop_file)

setup(
    name='spaceship-control',
    version='0.1',
    install_requires=requirements,
    packages=packages,
    package_dir={

        'spaceship_control': 'src',
        'spaceship_control.forms': 'forms',
        'spaceship_control.examples': 'examples',
        'spaceship_control.docs': 'docs',
    },
    package_data={

        'spaceship_control.forms': ['*.ui'],
        'spaceship_control.examples.ships':
            ['*.toml', '*.json', '*.yml', '*.yaml'],
        'spaceship_control.examples.scenarios':
            ['*.toml', '*.json', '*.yml', '*.yaml'],
        'spaceship_control.examples.objects':
            ['*.toml', '*.json', '*.yml', '*.yaml'],
        'spaceship_control.examples.images': ['*.png'],
        'spaceship_control.examples.controllers': ['*.py'],
        'spaceship_control.examples.controllers.lib': ['*.py'],
        'spaceship_control.docs': ['*/**/*']
    },
    entry_points={

        'gui_scripts': [
            'spaceshipcontrol = spaceship_control.main:main',
        ]
    },
    data_files = [
        ('share/applications', [TEMP_DESKTOP_FILE]),
        ('share/icons', ['imgs/spaceshipcontrol.png'])
    ],
    cmdclass={'install': OverrideInstall},
    license='LGPL-3.0'
)

os.remove(TEMP_DESKTOP_FILE)

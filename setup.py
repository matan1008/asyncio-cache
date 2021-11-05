from pathlib import Path

from setuptools import setup, find_packages

BASE_DIR = Path(__file__).parent.resolve(strict=True)
VERSION = '0.0.1'
PACKAGE_NAME = 'asyncio_cache'
PACKAGES = [p for p in find_packages() if not p.startswith('tests')]


def get_description():
    return (BASE_DIR / 'README.md').read_text()


if __name__ == '__main__':
    setup(
        version=VERSION,
        name=PACKAGE_NAME,
        description='A python library for asyncio caches (like functools cache and lru_cache)',
        long_description=get_description(),
        long_description_content_type='text/markdown',
        cmdclass={},
        packages=PACKAGES,
        author='Matan Perelman',
        classifiers=[
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
        ],
        url='https://github.com/matan1008/asyncio-cache',
        project_urls={
            'asyncio-cache': 'https://github.com/matan1008/asyncio-cache'
        },
        tests_require=['pytest', 'pytest-asyncio'],
    )

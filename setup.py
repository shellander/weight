from setuptools import setup

setup(
    name='weight',
    version='0.1',
    py_modules=['weight'],
    install_requires=[
        'click',
        'asciichartpy',
        'tabulate'
    ],
    packages=['mllineplot'],
    entry_points={
        'console_scripts': [
            'weight = weight:cli',
        ],
    },
)
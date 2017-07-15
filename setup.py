import sys

import setuptools

needs_pytest = {'pytest', 'test', 'ptr'}.intersection(sys.argv)
setup_requires = ['pytest-runner'] if needs_pytest else []

setuptools.setup(
    name='ws-nat',
    python_requires='>=3.5',
    install_requires=['aiohttp'],
    setup_requires=setup_requires,
    tests_require=['pytest', 'pytest-aiohttp'],
    entry_points={
        'console_scripts': [
            'intermediate-server=ws_nat.intermediate_server:run',
            'sender=ws_nat.sender:run',
            'receiver=ws_nat.receiver:run'
        ]
    }
)

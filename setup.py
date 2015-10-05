# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

import sys


with open('README.rst') as f:
    description = f.read()

install_requires = [
    'docopt>=0.6.1',
    'kazoo>=1.3.1',
    'kombu>=3.0.16',
    'gevent',
    'msgpack-python>=0.4.0',
    'psutil>=2.1.1',
    'PyYAML>=3.11',
    'pyzmq>=14.3.0',
    'redis>=2.9.1',
    'setproctitle>=1.1.8',
    'six>=1.6',
    'Werkzeug>=0.10.4',
    'blessings>=1.5.1',
    'netifaces>=0.10.4',
    'mock>=1.0.1',
    'PyHamcrest>=1.8.2',
    'pytz',
    'iso8601>=0.1.10',
]

if sys.version_info.major == 2:
    install_requires.append('Monotime>=1.0')
elif sys.version_info.major == 3:
    install_requires.remove('gevent')
    install_requires.append('gevent>=1.1a2')

setup(
    name='lymph',
    url='http://github.com/deliveryhero/lymph/',
    version='0.9.0',
    namespace_packages=['lymph'],
    packages=find_packages(),
    license=u'Apache License (2.0)',
    author=u'Delivery Hero Holding GmbH',
    maintainer=u'Johannes Dollinger',
    maintainer_email=u'johannes.dollinger@deliveryhero.com',
    description=u'a service framework',
    long_description=description,
    include_package_data=True,
    install_requires=install_requires,
    extras_require={
        'sentry': ['raven'],
        'newrelic': ['newrelic'],
    },
    entry_points={
        'console_scripts': ['lymph = lymph.cli.main:main'],
        'lymph.cli': [
            'discover = lymph.cli.discover:DiscoverCommand',
            'emit = lymph.cli.emit:EmitCommand',
            'help = lymph.cli.help:HelpCommand',
            'inspect = lymph.cli.inspect:InspectCommand',
            'instance = lymph.cli.service:InstanceCommand',
            'list = lymph.cli.list:ListCommand',
            'node = lymph.cli.service:NodeCommand',
            'request = lymph.cli.request:RequestCommand',
            'shell = lymph.cli.shell:ShellCommand',
            'subscribe = lymph.cli.subscribe:SubscribeCommand',
            'tail = lymph.cli.tail:TailCommand',
            'config = lymph.cli.config:ConfigCommand',
            'worker = lymph.cli.service:WorkerCommand',
        ],
        'nose.plugins.0.10': ['lymph = lymph.testing.nose:LymphPlugin'],
        'pytest11': ['lymph = lymph.testing.pytest'],
        'kombu.serializers': [
            'lymph-json = lymph.serializers.kombu:json_serializer_args',
            'lymph-msgpack = lymph.serializers.kombu:msgpack_serializer_args',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3'
    ]
)

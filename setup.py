# -*- coding: utf-8 -*-
from setuptools import setup, find_packages


with open('README.rst') as f:
    description = f.read()


setup(
    name='iris',
    url='http://github.com/deliveryhero/iris/',
    version='0.1.0',
    namespace_packages=['iris'],
    packages=find_packages(),
    license=u'Apache License (2.0)',
    author=u'Delivery Hero Holding GmbH',
    maintainer=u'Johannes Dollinger',
    maintainer_email=u'johannes.dollinger@deliveryhero.com',
    long_description=description,
    include_package_data=True,
    setup_requires=[
        'Cython>=0.20.1',
    ],
    install_requires=[
        'docopt>=0.6.1',
        'gevent>=1.1-dev',
        'kazoo>=1.3.1',
        'kombu>=3.0.16',
        'monotime>=1.0', # FIXME: only for Python 2
        'msgpack-python>=0.4.0',
        'psutil>=2.1.1',
        'PyYAML>=3.11',
        'pyzmq>=14.3.0',
        'redis>=2.9.1',
        'setproctitle>=1.1.8',
        'six>=1.6',
        'Werkzeug>=0.9.4',
        'blessings>=1.5.1',
    ],
    entry_points={
        'console_scripts': ['iris = iris.cli.main:main'],
        'iris.cli': [
            'help = iris.cli.help:HelpCommand',
            'list = iris.cli.base:ListCommand',
            'tail = iris.cli.tail:TailCommand',
            'instance = iris.cli.service:InstanceCommand',
            'node = iris.cli.service:NodeCommand',
            'request = iris.cli.request:RequestCommand',
            'discover = iris.cli.request:DiscoverCommand',
            'inspect = iris.cli.request:InspectCommand',
            'subscribe = iris.cli.request:SubscribeCommand',
            'emit = iris.cli.request:EmitCommand',
        ],
        'nose.plugins.0.10': ['iris = iris.testing.nose:IrisPlugin'],
        'pytest11': ['iris = iris.testing.pytest'],
        'kombu.serializers': [
            'iris-json = iris.serializers.kombu:json_serializer_args',
            'iris-msgpack = iris.serializers.kombu:msgpack_serializer_args',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
    ]
)

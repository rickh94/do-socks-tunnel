from setuptools import setup, find_packages

VERS = '0.1.0'
with open('README.rst', 'r') as readme:
    LONG_DESCRIPTION = readme.read()

setup(
    name='dosockstunnel',
    version=VERS,

    description=('Initializes socks tunnels to Digital Ocean droplets '
                 'on-the-fly'),
    long_description=LONG_DESCRIPTION,

    url='https://github.com/rickh94/do-socks-tunnel',
    author='Rick Henry',
    author_email='fredericmhenry@gmail.com',

    license='MIT',
    python_requires='>=3',


    py_modules=['dosockstunnel'],
    install_requires=[
        'python-digitalocean',
        'cryptography',
        'randomwords',
    ],
    tests_require=['pytest'],

    entry_points={
        'console_scripts': [
            'dosockstunnel = dosockstunnel:main'
        ],
    },
)

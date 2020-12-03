# =============================================================================
# SETUP.PY
# -----------------------------------------------------------------------------

from setuptools import setup

setup(
    name = 'mldeploy',
    packages = ['mldeploy'],
    version = '0.1',
    license='MIT',
    description = 'Deploy ML code to cloud resources as a REST API for inference and training.',
    author = 'Lee MacKenzie Fischer',
    author_email = 'lee.m.fischer@protonmail.com',
    url = 'https://github.com/kingfischer16/mldeploy',
    download_url = 'https://github.com/user/reponame/archive/v_01.tar.gz',
    keywords = [
        'machine-learning', 'rest-api', 'aws', 'docker', 'deployment', 'cloud'
    ],
    install_requires = ['docker', 'fire', 'ruamel.yaml'],
    entry_points = {
        'console-scripts': ['mldeploy=mldeploy.cli:main']
    },
    classifiers = [
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'Intended Audience :: Information Technology',
    'Intended Audience :: Science/Research',
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    ]
)

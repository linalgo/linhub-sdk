from setuptools import setup

setup(
    name='linalgo',
    packages=['linalgo'],
    description=('Python library for Natural Language Processing supporting '
                 'the open annotation standard'),
    version='0.1',
    author='Arnaud Rachez',
    author_email='arnaud@linalgo.com',
    requires=['numpy', 'scipy'],
)

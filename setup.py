from setuptools import setup

setup(
    name='linalgo',
    description=('Python library for Natural Language Processing supporting '
                 'the open annotation standard'),
    version='0.0',
    author='Arnaud Rachez',
    author_email='arnaud@linalgo.com',
    packages=['linalgo'],
    requires=['numpy', 'scipy'],
)

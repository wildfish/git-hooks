from setuptools import setup

setup(
    name='git-hooks',
    version='',
    packages=['githooks'],
    url='https://github.com/OmegaDroid/git-hooks',
    license='MIT',
    author='Dan Bate',
    author_email='dan.bate@gmail.com',
    description='Package manager for installing git commit hooks',
    include_package_data=True,
    package_data={
        'githooks/hook_scripts': ['*']
    }
)

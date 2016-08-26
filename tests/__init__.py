from os import environ

from hypothesis import settings

settings.register_profile('dev', settings(max_examples=10))
settings.register_profile('ci', settings())


if environ.get('CI', False):
    settings.load_profile('ci')
else:
    settings.load_profile('dev')

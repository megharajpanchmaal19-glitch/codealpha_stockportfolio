"""
test_settings.py — Settings override for running tests WITHOUT XAMPP/MySQL.

Usage:
    python manage.py test portfolio --settings=config.test_settings --verbosity=2

All production settings are inherited from config.settings.
Only the DATABASES key is replaced with in-memory SQLite.
"""

from .settings import *   # noqa: F401,F403  inherit everything

# Override database with in-memory SQLite for fast, offline tests.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME':   ':memory:',
    }
}

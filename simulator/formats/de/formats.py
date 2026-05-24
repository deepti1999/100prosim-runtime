"""Custom German number + date formats per stakeholder PDF §2.5.2.

Overrides Django's built-in ``de`` locale. Only the symbols that differ
from the default ``de`` locale are listed here; Django falls back to the
upstream ``de`` format for anything not defined.
"""

# Number format — dot for thousands grouping, comma as decimal separator.
DECIMAL_SEPARATOR = ','
THOUSAND_SEPARATOR = '.'
NUMBER_GROUPING = 3

# Date / time formats — standard German conventions.
DATE_FORMAT = 'd.m.Y'
TIME_FORMAT = 'H:i'
DATETIME_FORMAT = 'd.m.Y H:i'
SHORT_DATE_FORMAT = 'd.m.Y'
SHORT_DATETIME_FORMAT = 'd.m.Y H:i'
FIRST_DAY_OF_WEEK = 1  # Monday

# Input formats — accept German formats for form fields.
DATE_INPUT_FORMATS = [
    '%d.%m.%Y',
    '%d.%m.%y',
    '%Y-%m-%d',
]
DATETIME_INPUT_FORMATS = [
    '%d.%m.%Y %H:%M',
    '%d.%m.%Y %H:%M:%S',
    '%Y-%m-%d %H:%M:%S',
    '%Y-%m-%d %H:%M',
]
TIME_INPUT_FORMATS = [
    '%H:%M',
    '%H:%M:%S',
]

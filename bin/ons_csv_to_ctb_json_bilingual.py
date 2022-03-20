"""Bilingual and BilingualDict are classes which contain English and Welsh values."""


class Bilingual:
    """Bilingual has an English value and a Welsh value."""

    def __init__(self, english, welsh):
        """Initialize Bilingual object."""
        self._english = english
        if welsh:
            self._welsh = welsh
        else:
            self._welsh = english

    def english(self):
        """Return English version of value."""
        return self._english

    def welsh(self):
        """Return Welsh version of value."""
        return self._welsh


class BilingualDict(Bilingual):
    """Collection of fields some or all of which may have English/Welsh values."""

    def __init__(self, data, private=None):
        """Initialize BilingualDict object. The data variable is modified by this method."""
        self.private = private
        welsh = {}
        localize_dict(data, welsh)
        Bilingual.__init__(self, data, welsh)


def localize(original, welsh, key_index, value):
    """
    Resolve the translations or call localize_dict/localize_list.

    Values in the original object are overwritten with English values, whilst equivalent fields
    are added to the Welsh object.
    """
    if value is None or isinstance(value, str):
        welsh[key_index] = value
    elif isinstance(value, (Bilingual)):
        original[key_index] = value.english()
        welsh[key_index] = value.welsh()
    elif isinstance(value, dict):
        welsh[key_index] = dict()
        localize_dict(value, welsh[key_index])
    elif isinstance(value, list):
        welsh[key_index] = [None] * len(value)
        localize_list(value, welsh[key_index])
    else:
        raise ValueError(f'Unexpected type {type(value)} for {key_index}:{value}')


def localize_dict(original, welsh):
    """Call localize on each element in a dict."""
    for key, value in original.items():
        localize(original, welsh, key, value)


def localize_list(original, welsh):
    """Call localize on each element in a list."""
    for index, value in enumerate(original):
        localize(original, welsh, index, value)

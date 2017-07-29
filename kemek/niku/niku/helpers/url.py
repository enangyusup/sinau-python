# -*- coding: utf-8 -*-
from re import compile

from jinja2 import Markup
from werkzeug.routing import BaseConverter

from niku.models.core import Article


_slug_re1 = compile(r'[^\w\/+| -]')
_slug_re2 = compile(r'[^\w]')


def create_slug(title):
    slug = Markup(title.lower()).striptags()
    slug = _slug_re1.sub('', slug)
    slug = ' '.join(slug.split()).strip()
    slug = _slug_re2.sub('-', slug)

    if _available(slug):
        return slug

    n = 1
    while True:
        _slug = '{0}-{1}'.format(slug, n)
        if _available(_slug):
            slug = _slug
            break
        n += 1
    return slug


def _available(slug):
    exist = Article.query.filter_by(slug=slug).first()
    if exist:
        return False
    return True


class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]

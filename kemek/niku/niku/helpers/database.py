# -*- coding: utf-8 -*-
from __future__ import division
from math import ceil

from flask import abort
from sqlalchemy import func

from niku import db_session


def find_or_create(model, **kwargs):
    obj = model.query.filter_by(**kwargs).first()
    if obj:
        return obj
    obj = model(**kwargs)
    return obj


def find_or_404(model, **kwargs):
    rv = model.query.filter_by(**kwargs).first()
    if rv is None:
        abort(404)
    return rv


def get_or_404(model, ident):
    rv = model.query.get(ident)
    if rv is None:
        abort(404)
    return rv


class Pagination(object):
    def __init__(self, model, page=1, per_page=20):
        self._model = model
        self.page = page
        self.per_page = per_page
        self.query = model.query

    @property
    def items(self):
        offset = (self.page - 1) * self.per_page
        rv = self.query.order_by('id desc').\
                        offset(offset).\
                        limit(self.per_page)
        return rv

    @property
    def max_page(self):
        rv = db_session.query(func.count(self._model.id)).first()
        max_records = rv[0]
        return int(ceil(max_records / self.per_page))

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def page_prev(self):
        if self.has_prev:
            return self.page - 1
        return None

    @property
    def has_next(self):
        return self.page < self.max_page

    @property
    def page_next(self):
        if self.has_next:
            return self.page + 1
        return None

    def pages(self, left=2, right=2):
        # itung ndiri!
        total_pages = 1 + left + right
        if self.page <= left + 1:
            return xrange(1, total_pages + 1)
        if self.page + right >= self.max_page:
            return xrange(self.max_page - total_pages, self.max_page + 1)
        else:
            return xrange(self.page - left, self.page + right + 1)

# -*- coding: utf-8 -*-
from flask.ext.wtf import Form, DateTimeField, StringField, \
                          TextAreaField, HiddenField, Required


class ArticleForm(Form):
    id = HiddenField()
    title = StringField('Title', validators=[Required()])
    slug = StringField('Permalink')
    published_time = DateTimeField('Published Time')
    shortdesc = TextAreaField('Short Description')
    content = TextAreaField('Content')

# -*- coding: utf-8 -*-
from flask import render_template, redirect, url_for

from niku.models.core import Article
from niku.helpers.database import get_or_404, Pagination
from niku_cms.app import app
from niku_cms.models.forms import ArticleForm


@app.route('/articles/')
@app.route('/articles/<int:page>/')
def articles(page=1):
    """listing artikel yang ada"""
    pagination = Pagination(Article, page=page)
    return render_template('articles.html', pagination=pagination)


@app.route('/article/')
@app.route('/article/<int:id>/')
def article(id=None):
    """display form artikel, no id: add, with id: edit"""
    article = None
    if id:
        article = get_or_404(Article, id)
    form = ArticleForm(obj=article)
    return render_template('article.html', article=article, form=form)


@app.route('/article/', methods=['POST'])
def article_post():
    """ngeproses segala form yang berkaitan dengan artikel"""
    return redirect(url_for('articles'))

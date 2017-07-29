# -*- coding: utf-8 -*-
from flask import Flask, render_template

from niku import db_session
from niku.models.core import Site, Article
from niku.helpers.url import RegexConverter
from niku.blueprints.article import article


app = Flask('niku_berita')
app.url_map.converters['re'] = RegexConverter
app.register_blueprint(article)

@app.teardown_request
def shutdown_session(exception=None):
    db_session.remove()


@app.route('/')
def index():
    news = Site.query.filter_by(name='news').first()
    terkini = Article.query.filter_by(site=news, published=True).\
                            order_by('published_time desc').\
                            limit(20)

    ekonomi = Article.query.filter_by(published=True).\
                            join(Article.tags).\
                            filter_by(name='ekonomi').\
                            order_by('published_time desc').\
                            limit(5)

    return render_template('index.html', terkini=terkini, ekonomi=ekonomi)


if __name__ == '__main__':
    app.run(debug=True)

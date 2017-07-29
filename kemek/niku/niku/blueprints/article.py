# -*- coding: utf-8 -*-
from flask import Blueprint, abort, request, redirect, render_template

from niku.models.core import Article
from niku.helpers.database import find_or_404, get_or_404


article = Blueprint('article', __name__)


@article.route('/<re("\d{4}"):year>/<re("\d{2}"):month>/<re("\d{2}"):day>/<slug>/')
def show_article(slug=None, year=None, month=None, day=None):
    article = find_or_404(Article, slug=slug)
    # kalau slug ada, tapi tanggal salah, redirect ke tanggal yang benar
    url_date = '{} {} {}'.format(year, month, day)
    article_date = '{:%Y %m %d}'.format(article.published_time)
    if url_date != article_date:
        return redirect(article.url, 301)
    # kalau oke, buka artikel
    return render_template('article.html', article=article)


## redirect url-url kuno
def redirect_article(id):
    article = get_or_404(Article, id)
    if article.published:
        return redirect(article.url, 301)
    abort(404)


# http://www.liputan6.com/news/?id=49846
# http://www.liputan6.com/fullnews/?id=31525
@article.route('/news/')
@article.route('/fullnews/')
def redirect_1():
    id = request.args.get('id')
    return redirect_article(id)


# http://www.liputan6.com/fullnews/76075.html
# http://berita.liputan6.com/ibukota/201010/299467/Awas.Pohon.Tumbang
@article.route('/fullnews/<int:id>.html')
@article.route('/<re("[a-z]+"):category>/<re("\d{6}"):month>/<int:id>/<slug>')
def redirect_2(id=None, category=None, month=None, slug=None):
    return redirect_article(id)


# http://www.liputan6.com/view/9,108911,1,0,1127291118.html
@article.route('/view/<something>.html')
def redirect_3(something):
    id = something.split(',')[1]
    return redirect_article(id)


# http://www.liputan6.com/ekbis/?id=177655
# TODO: listing kategori yang pernah ada, menghindari tabrakan dengan
# url yang baru
@article.route('/sesuatu-yang-merepotkan')
def redirect_4():
    return 'repot'


# http://berita.liputan6.com/read/353365/
# http://showbiz.liputan6.com/read/345518/amy-winehouse-ditemukan-tewas
@article.route('/read/<int:id>/')
@article.route('/read/<int:id>/<slug>')
def redirect_5(id=None, slug=None):
    return redirect_article(id)

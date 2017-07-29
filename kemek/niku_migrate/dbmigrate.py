# -*- coding: utf-8 -*-
import re
import json
#import logging

from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from jinja2 import Markup
from html5tidy import tidy
from ftfy import fix_text

from niku import db_session
from niku.models.core import Site, Article
from niku.helpers.url import create_slug


engine = create_engine('mysql+oursql://enang:yusup@localhost/liputan6_xxx?charset=latin1')
conn = engine.connect()


#logging.basicConfig(filename='migration.log')
#logger = logging.getLogger('sqlalchemy.engine')
#logger.setLevel(logging.DEBUG)

# buat koleksi
urls_txt = open('urls.txt', 'w')


def get_ids():
    result = conn.execute("select id from tbl_news")
    ids = [row[0] for row in result]
    return sorted(ids)


def get_cats():
    result = conn.execute("select c.cat_id, c.cat_name, ch.channel_name \
                           from tbl_category as c, tbl_channel as ch \
                           where c.channel_id=ch.channel_id")
    # FIXME: row[1] == nama kategori, dipake buat salah satu tag
    # apakah bener di lower() atau tidak, tentukan dulu
    cats = dict((row[0], [row[2].lower(), row[1].lower()]) for row in result)
    return cats


def get_news(id):
    result = conn.execute("select * from tbl_news where id = ?", id)
    row = result.fetchone()
    return row


def clean_html(text):
    # banyak link ngaco di dalam berita, bersihin dulu
    text = re.sub(r'<a href=([^>"]+)>', r'<a href="\1">', text)
    text = re.sub(r'<a href="([\S]+)[\s]+">', r'<a href="\1">', text)
    text = text.replace('http:http', 'http')
    text = text.replace('http:// http://', 'http://')
    # baru mulai mengurus isi
    text = fix_text(text.strip())
    try:
        text = tidy(text, fragment=True, encoding='utf-8')
    except UnicodeDecodeError:
        pass
    # kenapa banyak banget backtick? it should be single quote!
    text = text.replace("`", "'")
    # sebenernya sih: http://html5doctor.com/i-b-em-strong-element/
    # tapi demi konsistensi sama ckeditor...
    # FIXME: it's better to fix this in ckeditor instead
    text = text.replace('<i>', '<em>').replace('</i>', '</em>')
    text = text.replace('<b>', '<strong>').replace('</b>', '</strong>')
    try:
        text = Markup(text.decode('utf-8', 'replace')).unescape()
    except UnicodeEncodeError:
        # isinya apa sebenernya, udah diginiin, masih aja error nyink!
        pass
    # satu link lagi, terlalu aneh buat diedit di depan, harus belakangan
    text = re.sub(r'[\\"]+(http://[\w/.-]+)[\\"]+', r'"\1"', text)
    return text


_junk_re1 = re.compile(r'[^\w&\- ]')
_junk_re2 = re.compile(r'^(soal|fokus|kasus)')


def clean_tag(tag):
    try:
        tag = Markup(fix_text(tag.decode('utf-8'))).striptags()
    except UnicodeEncodeError:
        return None
    tag = _junk_re1.sub('', tag).strip()
    tag = _junk_re2.sub('', tag).strip()

    if not tag:
        return None
    if len(tag) < 3:
        return None
    if len(tag) > 40:
        return None
    if tag.isdigit():
        return None
    return tag


def migrate():
    # old db
    cats = get_cats()
    ids = get_ids()

    # new db
    top = Site.query.filter_by(name='top').first()
    news = Site.query.filter_by(name='news').first()
    showbiz = Site.query.filter_by(name='showbiz').first()
    bola = Site.query.filter_by(name='bola').first()
    health = Site.query.filter_by(name='health').first()
    tekno = Site.query.filter_by(name='tekno').first()

    # cek id terakhir yang sudah masuk di db baru
    last_article = Article.query.order_by('id desc').first()
    last_id = last_article.id if last_article else None

    for id in ids:
        # kalau udah ada di db baru, skip
        if id <= last_id:
            continue

        # normal: ambil data di db lama
        _news = get_news(id)

        try:
            kanal = cats[_news.cat_id][0]
            kategori = cats[_news.cat_id][1]
        except KeyError:
            # cat_id ngegantung tanpa kanal. channel_id 11 ada di mana?
            site = top
        else:
            if kanal in ['berita', 'buser']:
                if kategori == 'olah raga':
                    site = bola
                else:
                    site = news
            elif kanal in ['showbiz', 'musik']:
                site = showbiz
            elif kanal in ['sport', 'bola']:
                site = bola
            elif kanal == 'kesehatan':
                site = health
            elif kanal == 'tekno':
                site = tekno
            else:
                # otomotif, gayahidup, pemilu, citizen6
                site = top

        try:
            migrate_article(site, _news, kategori)
        except IntegrityError:
            # kita bukan makhluk dengan integritas!
            pass

    urls_txt.close()


_href_re = re.compile(r'href="([\w:/,.?=-]+")>')


def migrate_article(site, news, cat_name):
    # buang berita yang tadinya tidak dipublish
    if news.publish == '0':
        return

    # buang bekasan scmusik.com, tidak valid!
    if news.title in ['About Us', 'Site Map', 'FAQ',
                      'Term Of Service', 'Contact Us']:
        return

    # bersihkan title berita yang mau diproses
    title = clean_html(news.title)

    # unpublish berita dari kanal-kanal yang musnah
    if site.name == 'top':
        published = False

    # unpublish berita-berita cuma selintas - 60 detik
    elif '60 Detik' in title or \
            title.startswith('Intisari Liputan') or \
            title in ['Lintas Daerah', 'Lintas Ekbis',
                      'Lintas Olahraga', 'Ragam Hiburan',
                      'Kriminal Sepekan', 'Kriminalitas Sepekan']:
        published = False
    else:
        published = True

    # cuma bikin slug buat berita yang dipublish
    if published:
        slug = create_slug(title)
    else:
        slug = None

    # shortdesc & content, bersihin dulu sebisanya
    shortdesc = clean_html(news.shortdesc)
    content = clean_html(news.news)

    # fix masalah date yang naudzubillah randomnnya
    if news.modified:
        published_time = news.publish_date
        last_modified = news.modified
    elif news.publish_date:
        published_time = news.publish_date
        last_modified = news.publish_date
    else:
        published_time = news.dates
        last_modified = news.dates

    article = Article(id=news.id,
                      site=site,
                      title=title,
                      slug=slug,
                      shortdesc=shortdesc,
                      content=content,
                      published=published,
                      published_time=published_time,
                      last_modified=last_modified
                     )
    db_session.add(article)

    #### tags
    # merge isi kategori, prehead, terkait, keyword ke dalam satu list
    _tags1 = [cat_name]
    for words in [news.prehead, news.terkait, news.keyword]:
        if not words:
            continue
        _tags1 += words.split(',')

    # demi konsistensi: lowercase them all
    # FIXME: is this the right decision?
    _tags2 = [tag.lower() for tag in _tags1]

    ## tag tambahan
    # cat_id di bawah ini diambil dari tbl_category, cat_parent == 4
    if news.cat_id in ['94', '95', '96', '97', '98', '99',
                       '100', '101', '102', '103']:
        _tags2.append('ekonomi')

    # bener gak ini masuk peristiwa?
    if news.cat_id in [2, 3, 6, 7, 9]:
        _tags2.append('peristiwa')

    # kanal musik masuk ke showbiz, kategori musik
    if news.cat_id in ['37', '38', '39', '40', '41', '42',
                       '43', '44', '45', '86', '109', '123']:
        _tags2.append('musik')

    # daerah & ibukota itu berita nasional kan ya?
    for word in ['daerah', 'ibu kota', 'ibukota']:
        if word in _tags2:
            _tags2.append('nasional')

   # rename tag yang mesti direname
    _tags3 = []
    for tag in _tags2:
        tag = clean_tag(tag)
        if not tag:
            continue
        if tag in ['berita', 'lain-lain']:
            continue
        if tag == 'ekonomi & bisnis':
            tag = 'ekonomi'
        elif tag == 'luar negeri':
            tag = 'internasional'
        elif tag == 'ibu kota':
            tag = 'ibukota'
        elif tag.startswith('prediksi'):
            tag = 'prediksi'
        _tags3.append(tag)

    # buang duplikasi tag
    _tags4 = list(set(_tags3))

    # and insert 'em
    article.str_tags = _tags4

    db_session.commit()

    # terakhir, ngegrep url dari content, buat koleksi
    link = _href_re.findall(article.content)
    if link:
        js = json.dumps((news.id, link))
        urls_txt.write(js + '\n')

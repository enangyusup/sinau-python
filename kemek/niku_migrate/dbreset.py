# -*- coding: utf-8 -*-
from niku import engine, db_session, Base
from niku.models.core import Site, Tag


def create():
    Base.metadata.create_all(bind=engine)


def drop():
    Base.metadata.drop_all(bind=engine)


def populate():
    db_session.add_all([
        Site(name='top', domain='liputan6.com'),
        Site(name='news', domain='berita.liputan6.com'),
        Site(name='showbiz', domain='showbiz.liputan6.com'),
        Site(name='bola', domain='liputanbola.com'),
        Site(name='health', domain='health.liputan6.com'),
        Site(name='tekno', domain='tekno.liputan6.com'),
        Site(name='video', domain='video.liputan6.com')
        ])
    db_session.add_all([
        Tag(name='politik'),
        Tag(name='peristiwa'),
        Tag(name='ekonomi'),
        Tag(name='nasional'),
        Tag(name='internasional')
        ])
    db_session.commit()


def reset():
    drop()
    create()
    populate()

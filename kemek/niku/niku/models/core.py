# -*- coding: utf-8 -*-
from datetime import datetime

from sqlalchemy import Table, Boolean, Column, DateTime, Integer, String, \
                       Text, ForeignKey
from sqlalchemy.orm import relationship, backref

from niku import Base
from niku.helpers.database import find_or_create


class Site(Base):
    __tablename__ = 'sites'
    id = Column(Integer, primary_key=True)
    name = Column(String(15), nullable=False)
    domain = Column(String(30))
    description = Column(Text(300))


article_tags = Table('article_tags', Base.metadata,
    Column('article_id', Integer,
                         ForeignKey('articles.id', ondelete='cascade')),
    Column('tag_id', Integer,
                     ForeignKey('tags.id', ondelete='cascade'))
)


class Article(Base):
    __tablename__ = 'articles'
    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey('sites.id'), nullable=False)
    site = relationship('Site')
    title = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, index=True)
    shortdesc = Column(Text(400))
    content = Column(Text)
    published = Column(Boolean, default=False)
    published_time = Column(DateTime, index=True)
    last_modified = Column(DateTime, onupdate=datetime.now)
    tags = relationship('Tag', secondary=article_tags,
                               passive_deletes=True,
                               backref=backref('articles', lazy='dynamic'))

    @property
    def url(self):
        return 'http://{}/{:%Y/%m/%d}/{}/'.\
                    format(self.site.domain, self.published_time, self.slug)

    @property
    def str_tags(self):
        return [tag.name for tag in self.tags]

    @str_tags.setter
    def str_tags(self, value):
        # bersihin isi tags dulu
        while self.tags:
            del self.tags[0]
        # baru masukin lagi
        for tag in value:
            self.tags.append(find_or_create(Tag, name=tag))


class Tag(Base):
    __tablename__ = 'tags'
    id = Column(Integer, primary_key=True)
    name = Column(String(40), unique=True, nullable=False, index=True)

    def __init__(self, name):
        self.name = name


class Headline(Base):
    __tablename__ = 'headlines'
    id = Column(Integer, primary_key=True)
    site_id = Column(Integer, ForeignKey('sites.id'), nullable=False)
    site = relationship('Site')
    article_id = Column(Integer, ForeignKey('articles.id'), nullable=False)
    article = relationship('Article')

# -*- coding: utf-8 -*-
from cookielib import CookieJar, Cookie
import urllib

from mediapoisk.enumerations import OrderDirection, Genre, Country, Language
from util import phpserialize
from util.encoding import ensure_str


class AbstractSearchFilter:
    # noinspection PyShadowingBuiltins
    def __init__(self, section=None, format=None, people=None, studio=None, genres=None, countries=None, languages=None,
                 rating_min=None, rating_max=None, year_min=None, year_max=None, order_by=None, order_dir=None,
                 user_rating_min=None, user_rating_max=None, name=None, page_size=None):
        self.section = section
        self.format = format
        self.people = people
        self.studio = studio
        self.genres = genres or []
        self.countries = countries or []
        self.languages = languages or []
        self.rating_min = rating_min
        self.rating_max = rating_max
        self.user_rating_min = user_rating_min
        self.user_rating_max = user_rating_max
        self.year_min = year_min
        self.year_max = year_max
        self.order_by = order_by
        self.order_dir = order_dir
        self.page_size = page_size
        self.name = name

    def as_tuple(self):
        return (self.section, self.format, self.people, self.studio, tuple(self.genres), tuple(self.countries),
                tuple(self.languages), self.rating_min, self.rating_max, self.user_rating_min, self.user_rating_max,
                self.year_min,  self.year_max, self.order_by, self.order_dir, self.page_size,
                self.name)

    @property
    def encoded_query(self):
        return dict((k, ensure_str(v)) for k, v in self.query.iteritems())

    @property
    def query(self):
        raise NotImplementedError

    def __hash__(self):
        return hash(self.as_tuple())

    def __ne__(self, other):
        return self.as_tuple() != other.as_tuple()

    def __eq__(self, other):
        return self.as_tuple() == other.as_tuple()


class MediaPoiskSearchFilter(AbstractSearchFilter):
    @property
    def settings(self):
        settings = {}
        if self.page_size:
            settings['media_per_page'] = self.page_size
        return settings

    @property
    def cookies(self):
        jar = CookieJar()
        if self.settings:
            jar.set_cookie(Cookie(
                version=0, name='settings',
                value=urllib.quote(phpserialize.serialize(self.settings)),
                port=None, port_specified=False, domain='mediapoisk.info',
                domain_specified=True, domain_initial_dot=True, path='/', path_specified=True, secure=False,
                expires=None, discard=True, comment=None, comment_url=None, rest=None, rfc2109=True
                ))
        return jar

    @property
    def query(self):
        query = {}
        if self.name:
            query['title'] = self.name
        if self.section:
            query['section'] = self.section.filter_val
        if self.format:
            query['form'] = self.format.filter_val
        if self.people:
            query['people'] = self.people
        if self.studio:
            query['studio'] = self.studio
        if self.genres:
            query['genre'] = ",".join(i.filter_val if i is Genre else unicode(i) for i in self.genres)
        if self.countries:
            query['made_in'] = ",".join(i.filter_val if i is Country else unicode(i) for i in self.countries)
        if self.languages:
            query['langs'] = ",".join(i.filter_val if i is Language else unicode(i) for i in self.languages)
        if self.rating_min:
            query['rating_from'] = self.rating_min
        if self.rating_max:
            query['rating_to'] = self.rating_max
        if self.user_rating_min:
            query['user_rating_from'] = self.user_rating_min
        if self.user_rating_max:
            query['user_rating_to'] = self.user_rating_max
        if self.year_min:
            query['year_from'] = str(self.year_min)
        if self.year_max:
            query['year_to'] = str(self.year_max)
        if self.order_by:
            query['order'] = self.order_by.filter_val
        if self.order_dir == OrderDirection.DESC:
            query['reverse'] = 'yes'
        return query

    def __str__(self):
        return "MediaPoiskSearchFilter"+repr(self.query)

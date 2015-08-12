# -*- coding: utf-8 -*-

from mediapoisk.plugin import plugin
from search import make_search
from common import with_fanart
from mediapoisk.enumerations import Section, Format, Genre, Country, Language, Order, OrderDirection
from mediapoisk.common import notify, lang
from xbmcswift2 import xbmcgui, ensure_unicode

import titleformat as tf
import mediapoisk.container as container


@plugin.route('/advanced_search/clear')
def clear_advanced_search():
    storage = container.search_storage()
    storage['search_filter'] = container.search_filter()


@plugin.route('/advanced_search/<section>/do')
def do_advanced_search(section):
    plugin.set_content('movies')
    storage = container.search_storage()
    sf = storage['search_filter']
    """:type : AbstractSearchFilter"""
    sf.section = Section.find(section)
    if not make_search(sf):
        notify(lang(40313))
        plugin.finish(succeeded=False)


@plugin.route('/advanced_search/edit/<param>')
def edit_advanced_search(param):
    storage = container.search_storage()
    sf = storage['search_filter']
    """:type : AbstractSearchFilter"""
    if param == 'name':
        res = xbmcgui.Dialog().input(lang(34116))
        sf.name = ensure_unicode(res) if res else None
    elif param == 'people':
        res = xbmcgui.Dialog().input(lang(34118))
        sf.people = ensure_unicode(res) if res else None
    elif param == 'studio':
        res = xbmcgui.Dialog().input(lang(34119))
        sf.studio = ensure_unicode(res) if res else None
    elif param == 'format':
        formats = sorted(Format.all())
        res = xbmcgui.Dialog().select(lang(34100), [lang(34101)] + [f.localized for f in formats])
        sf.format = formats[res - 1] if res else None
    elif param == 'genre':
        genres = sorted(Genre.all())
        res = xbmcgui.Dialog().select(lang(34103), [lang(34101)] + [g.localized for g in genres])
        sf.genres = [genres[res - 1]] if res else []
    elif param == 'genre_text':
        res = xbmcgui.Dialog().input(lang(34103))
        sf.genres = [t.strip() for t in ensure_unicode(res).split(",")] if res else []
    elif param == 'country':
        countries = sorted(Country.all())
        res = xbmcgui.Dialog().select(lang(34104), [lang(34101)] + [g.localized for g in countries])
        sf.countries = [countries[res - 1]] if res else []
    elif param == 'language':
        languages = sorted(Language.all())
        res = xbmcgui.Dialog().select(lang(34105), [lang(34101)] + [g.localized for g in languages])
        sf.languages = [languages[res - 1]] if res else []
    elif param == 'year_min':
        res = xbmcgui.Dialog().numeric(0, lang(34109))
        sf.year_min = int(res) if res else None
    elif param == 'year_max':
        res = xbmcgui.Dialog().numeric(0, lang(34110))
        sf.year_max = int(res) if res else None
    elif param == 'rating_min':
        res = xbmcgui.Dialog().numeric(0, lang(34112))
        if res and int(res) > 99:
            res = 99
        sf.rating_min = float(res) / 10.0 if res else None
    elif param == 'rating_max':
        res = xbmcgui.Dialog().numeric(0, lang(34113))
        if res and int(res) > 99:
            res = 99
        sf.rating_max = float(res) / 10.0 if res else None
    elif param == 'order_by':
        orders = Order.all()
        res = xbmcgui.Dialog().select(lang(34114), [lang(34101)] + [g.localized for g in orders])
        sf.order_by = orders[res - 1] if res else None
    elif param == 'order_dir':
        dirs = OrderDirection.all()
        res = xbmcgui.Dialog().select(lang(34115), [g.localized for g in dirs])
        sf.order_dir = OrderDirection.DESC if res == 1 else None


@plugin.route('/advanced_search/<section>')
def advanced_search(section):
    section = Section.find(section)
    storage = container.search_storage()
    sf = storage.setdefault('search_filter', container.search_filter())
    """:type : AbstractSearchFilter"""
    items = [{
        'label': lang(34102),
        'path': plugin.url_for('do_advanced_search', section=section.filter_val),
    }, {
        'label': lang(34111),
        'path': plugin.url_for('clear_advanced_search'),
    }, {
        'label': tf.color(lang(34116), 'white') + ": " + (sf.name if sf.name else lang(34117)),
        'path': plugin.url_for('edit_advanced_search', param='name')
        # }, {
        #     'label': tf.color(lang(34118), 'white') + ": " + (sf.people if sf.people else lang(34117)),
        #     'path': plugin.url_for('edit_advanced_search', param='people')
    }, {
        'label': tf.color(lang(34119), 'white') + ": " + (sf.studio if sf.studio else lang(34117)),
        'path': plugin.url_for('edit_advanced_search', param='studio')
    }, {
        'label': tf.color(lang(34100), 'white') + ": " + (unicode(sf.format) if sf.format else lang(34101)),
        'path': plugin.url_for('edit_advanced_search', param='format')
    }, {
        'label': tf.color(lang(34103), 'white') + ": " + (", ".join(unicode(g) for g in sf.genres)
                                                          if sf.genres else lang(34101)),
        'path': plugin.url_for('edit_advanced_search', param='genre' if section != Section.ANIME else 'genre_text')
    }, {
        'label': tf.color(lang(34104), 'white') + ": " + (", ".join(unicode(c) for c in sf.countries)
                                                          if sf.countries else lang(34101)),
        'path': plugin.url_for('edit_advanced_search', param='country')
    }, {
        'label': tf.color(lang(34105), 'white') + ": " + (", ".join(unicode(l) for l in sf.languages)
                                                          if sf.languages else lang(34101)),
        'path': plugin.url_for('edit_advanced_search', param='language')
    }, {
        'label': tf.color(lang(34109), 'white') + ": " + (str(sf.year_min) if sf.year_min else lang(34101)),
        'path': plugin.url_for('edit_advanced_search', param='year_min')
    }, {
        'label': tf.color(lang(34110), 'white') + ": " + (str(sf.year_max) if sf.year_max else lang(34101)),
        'path': plugin.url_for('edit_advanced_search', param='year_max')
    }, {
        'label': tf.color(lang(34112), 'white') + ": " + (str(sf.rating_min) if sf.rating_min else lang(34101)),
        'path': plugin.url_for('edit_advanced_search', param='rating_min')
    }, {
        'label': tf.color(lang(34113), 'white') + ": " + (str(sf.rating_max) if sf.rating_max else lang(34101)),
        'path': plugin.url_for('edit_advanced_search', param='rating_max')
    }, {
        'label': tf.color(lang(34114), 'white') + ": " + (sf.order_by.localized if sf.order_by else lang(34101)),
        'path': plugin.url_for('edit_advanced_search', param='order_by')
    }, {
        'label': tf.color(lang(34115), 'white') + ": " + (
            OrderDirection.DESC.localized if sf.order_dir else OrderDirection.ASC.localized),
        'path': plugin.url_for('edit_advanced_search', param='order_dir')
    }]
    plugin.finish(with_fanart(items), cache_to_disc=False)

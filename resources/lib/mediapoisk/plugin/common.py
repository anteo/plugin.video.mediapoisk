# -*- coding: utf-8 -*-
from mediapoisk import container as container
from mediapoisk.common import filter_dict, date_to_str
from mediapoisk.enumerations import Section
from mediapoisk.plugin import plugin
from mediapoisk.plugin.contextmenu import search_result_context_menu, toggle_watched_context_menu, \
    refresh_context_menu, download_torrent_context_menu, library_context_menu, toggle_auto_refresh_context_menu
from mediapoisk.scraper import Details, Media, Folder, File
import titleformat as tf


def with_fanart(item, url=None):
    if isinstance(item, list):
        return [with_fanart(i, url) for i in item]
    elif isinstance(item, dict):
        properties = item.setdefault("properties", {})
        if not properties.get("fanart_image"):
            if not url:
                properties["fanart_image"] = plugin.addon.getAddonInfo("fanart")
            else:
                properties["fanart_image"] = url
        return item


def itemify_library_folder(d, f):
    """
    :type f: Folder
    """
    item = itemify_folder(f)
    item['label'] = tf.library_folder_title(d, f)
    item['info']['title'] = d.title
    item['context_menu'] += toggle_auto_refresh_context_menu(f.section, f.media_id)
    return item


def itemify_folder(f):
    """
    :type f: Folder
    :rtype: dict
    """
    item = {
        'label': tf.folder_title(f),
        'path': plugin.url_for('show_files', section=f.section.filter_val, media_id=f.media_id, folder_id=f.id),
        'context_menu':
            refresh_context_menu(f.media_id) +
            download_torrent_context_menu(f.link) +
            library_context_menu(f.section, f.media_id, f.id),
        'info': {
            'size': f.size,
        },
        'stream_info': {
            'video': {
                'width': f.fmt.width,
                'height': f.fmt.height,
            },
        }
    }
    return with_fanart(item)


def itemify_file(f, **kwargs):
    """
    :type f: File
    """
    item = {
        'label': tf.file_title(f),
        'context_menu':
            refresh_context_menu(f.media_id) +
            toggle_watched_context_menu() +
            download_torrent_context_menu(f.link),
        'is_playable': True,
        'stream_info': [('video', {
            'codec': f.file_format,
            'width': f.resolution[0],
            'height': f.resolution[1],
            'duration': f.duration,
        })],
        'path': plugin.url_for('play_file', section=f.section.filter_val, media_id=f.media_id,
                               url=f.link, title=f.title, **kwargs)
    }
    return with_fanart(item)


def itemify_details(details):
    """
    :type details: Details
    :rtype: dict
    """
    item = {
        'thumbnail': details.poster,
        'path': plugin.url_for('show_folders', section=details.section.filter_val, media_id=details.media_id),
        'info': filter_dict({
            'plot': details.plot,
            'title': details.title,
            'rating': details.rating,
            'cast': details.actors,
            'studio': u" / ".join(details.studios),
            'writer': u" / ".join(details.creators),
            'premiered': details.release_date_russia or details.release_date,
            'genre': u" / ".join(unicode(g) for g in details.genres),
            'year': details.year,
            'originaltitle': u" / ".join(details.original_title),
        })
    }
    return with_fanart(item)


def itemify_single_result(result, folders=None):
    """
    :type result: Details
    """
    media_id = result.media_id
    scraper = container.scraper()
    folders = folders or scraper.get_folders_cached(media_id)
    watched_items = container.watched_items()
    total_size = sum(f.size for f in folders)
    is_series = result.section.is_series()
    watched = watched_items.is_watched(media_id, total_size=total_size if is_series else None)
    meta_cache = container.meta_cache()
    meta = meta_cache.setdefault(media_id, {})
    meta.update({
        'total_size': total_size,
        'is_series': is_series,
    })
    item = itemify_details(result)
    item.update({
        'label': tf.bookmark_title(result, folders),
        'context_menu': search_result_context_menu(result, total_size=total_size),
    })
    item['info'].update({
        'playcount': int(watched),
    })
    return item


def itemify_search_results(section, results):
    """
    :type results: list[Media]
    """
    ids = [result.id for result in results]
    scraper = container.scraper()
    meta_cache = container.meta_cache()
    all_details = scraper.get_details_bulk(section, ids)
    watched_items = container.watched_items()
    items = []
    for media in results:
        details = all_details[media.id]
        is_series = details.section.is_series()
        watched = watched_items.is_watched(media.id, date_added=media.date if is_series else None)
        meta = meta_cache.setdefault(media.id, {})
        meta.update({
            'date_added': media.date,
            'is_series': is_series,
        })
        item = itemify_details(details)
        item.update({
            'label': tf.media_title(media),
            'label2': date_to_str(media.date),
            'context_menu': search_result_context_menu(details, media.date),
        })
        item['info'].update({
            'date': date_to_str(media.date),
            'playcount': int(watched),
        })
        items.append(item)
    return items


def itemify_bookmarks(bookmarks):
    scraper = container.scraper()
    by_section = {}
    for b in bookmarks:
        by_section.setdefault(b.section, []).append(b.media_id)
    details = {}
    folders = {}
    for section, ids in by_section.iteritems():
        details[section] = scraper.get_details_bulk(section, ids)
        folders[section] = scraper.get_folders_bulk(section, ids)
    return [itemify_single_result(details[b.section][b.media_id], folders[b.section][b.media_id]) for b in bookmarks]

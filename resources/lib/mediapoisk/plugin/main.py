# -*- coding: utf-8 -*-

from mediapoisk.plugin import plugin
from mediapoisk.common import lang, batch, abort_requested, save_files, purge_temp_dir, log
from mediapoisk.plugin.common import with_fanart, itemify_file, itemify_folder, \
    itemify_details, itemify_bookmarks, itemify_library_folder
from mediapoisk.enumerations import Section, Genre
from mediapoisk.plugin.search import make_search
from mediapoisk.plugin.contextmenu import toggle_watched_context_menu, bookmark_context_menu, \
    download_torrent_context_menu, clear_history_context_menu, library_context_menu
from util.encoding import ensure_unicode

import titleformat as tf
import mediapoisk.container as container


@plugin.route('/play/<section>/<media_id>/<url>/<title>')
def play_file(section, media_id, url, title):
    stream = container.torrent_stream()
    scraper = container.scraper()
    history = container.history()
    meta_cache = container.meta_cache()
    meta = meta_cache.setdefault(media_id, {})
    section = Section.find(section)
    details = scraper.get_details_cached(section, media_id)
    item = itemify_details(details)
    title = u"%s / %s" % (ensure_unicode(title), item['info']['title'])
    item['info']['title'] = title
    history.add(media_id, details.section, title, plugin.request.url, url, details.poster)
    history.storage.sync()
    torrent = container.torrent(url=url)
    player = container.player()

    def check_and_mark_watched(event):
        log.info("Playback event: %s, current player progress: %d", event, player.get_percent())
        if player.get_percent() >= 90 and plugin.request.arg('can_mark_watched'):
            watched_items = container.watched_items()
            watched_items.mark(media_id, date_added=meta.get('date_added'),
                               total_size=meta.get('total_size'))

    player.attach([player.PLAYBACK_STOPPED, player.PLAYBACK_ENDED], check_and_mark_watched)
    temp_files = stream.play(player, torrent, item)
    if temp_files:
        save_files(temp_files, rename=not stream.saved_files_needed, on_finish=purge_temp_dir)
    else:
        purge_temp_dir()


@plugin.route('/files/<section>/<media_id>/<folder_id>')
def show_files(section, media_id, folder_id):
    scraper = container.scraper()
    section = Section.find(section)
    plugin.set_content('movies')
    files = scraper.get_files_cached(section, media_id, folder_id)
    plugin.add_items(itemify_file(f) for f in files)
    plugin.finish(sort_methods=['unsorted', 'title', 'duration', 'size'])


@plugin.route('/folders/<section>/<media_id>')
def show_folders(section, media_id):
    section = Section.find(section)
    scraper = container.scraper()
    meta_cache = container.meta_cache()
    meta = meta_cache.setdefault(media_id, {})
    plugin.set_content('movies')
    folders = scraper.get_folders_cached(section, media_id)
    total_size = sum(f.size for f in folders)
    meta['total_size'] = total_size
    for f in folders:
        if len(f.files) == 1 and not meta.get('is_series'):
            item = itemify_file(f.files[0], can_mark_watched=1)
            item['label'] = tf.folder_file_title(f, f.files[0])
            item['context_menu'] += library_context_menu(section, media_id, f.id)
        else:
            item = itemify_folder(f)
        plugin.add_item(item)
    plugin.finish(sort_methods=['unsorted', 'title', 'duration', 'size'])


@plugin.route('/explore/<section>')
def explore(section):
    plugin.set_content('movies')
    section = Section.find(section)
    sf = container.search_filter(section)
    header = [
        {'label': lang(34000), 'path': plugin.url_for('search_index', section=section.filter_val)},
        {'label': lang(34001), 'path': plugin.url_for('genre_index', section=section.filter_val)}
        if section != Section.ANIME else None,
        {'label': lang(34002), 'path': plugin.url_for('bookmarks_index', section=section.filter_val)},
        {'label': lang(34011), 'path': plugin.url_for('history_index', section=section.filter_val)},
    ]
    header = [h for h in header if h is not None]
    make_search(sf, header)


@plugin.route('/genre/<section>')
def genre_index(section):
    return with_fanart([{'label': g.localized, 'path': plugin.url_for('by_genre', section=section, genre=g.name)}
                       for g in sorted(Genre.all())])


@plugin.route('/genre/<section>/<genre>')
def by_genre(section, genre):
    plugin.set_content('movies')
    section = Section.find(section)
    genre = Genre.find(genre) or unicode(genre)
    sf = container.search_filter(section, genres=[genre])
    make_search(sf)


@plugin.route('/bookmarks', options={'section': None}, name='global_bookmarks')
@plugin.route('/bookmarks/<section>')
def bookmarks_index(section):
    plugin.set_content('movies')
    section = Section.find(section)
    bookmarks = container.bookmarks().get(section)
    total = len(bookmarks)
    for b in batch(reversed(bookmarks)):
        if abort_requested():
            break
        items = itemify_bookmarks(b)
        plugin.add_items(items, total)
    plugin.finish(sort_methods=['unsorted', 'title', 'video_year', 'video_rating'], cache_to_disc=False)


@plugin.route('/history/clear')
def clear_history():
    history = container.history()
    history.clear()
    plugin.refresh()


@plugin.route('/history', options={'section': None}, name='global_history')
@plugin.route('/history/<section>')
def history_index(section):
    plugin.set_content('movies')
    section = Section.find(section)
    history = container.history()
    items = []
    for item in reversed(history.get(section)):
        items.append({
            'label': item.title,
            'thumbnail': item.poster,
            'path': item.path,
            'is_playable': True,
            'context_menu':
                toggle_watched_context_menu() +
                bookmark_context_menu(item.media_id, item.section, item.title) +
                download_torrent_context_menu(item.url) +
                clear_history_context_menu()
        })
    return with_fanart(items)


@plugin.route('/library')
def library_items():
    scraper = container.scraper()
    library_manager = container.library_manager()
    for section, media_ids in library_manager.stored_media_ids().items():
        for ids in batch(media_ids):
            if abort_requested():
                break
            all_folders = scraper.get_folders_bulk(section, ids)
            all_details = scraper.get_details_bulk(section, ids)
            items = [itemify_library_folder(all_details[media_id], f)
                     for media_id, folders in all_folders.iteritems()
                     for f in folders if library_manager.has_folder(f.id)]
            plugin.add_items(items)
    plugin.finish(sort_methods=['title'], cache_to_disc=False)


@plugin.route('/')
def index():
    items = [
        {'label': lang(34002), 'path': plugin.url_for('global_bookmarks')},
        {'label': lang(34011), 'path': plugin.url_for('global_history')},
    ]
    library_manager = container.library_manager()
    if library_manager.has_folders():
        items.append({'label': lang(34012), 'path': plugin.url_for('library_items')})
    items.extend({
        'label': tf.decorate(s.localized, bold=True, color='white'),
        'path': plugin.url_for('explore', section=s.name)
    } for s in Section)
    return with_fanart(items)


@plugin.route('/update_library')
def library_update():
    from mediapoisk.library import update_library
    update_library()
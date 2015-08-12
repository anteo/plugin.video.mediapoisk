# -*- coding: utf-8 -*-

from mediapoisk.common import singleton
from mediapoisk.plugin import plugin


@singleton
def file_transfer_progress():
    from mediapoisk.xbmcstuff import XbmcFileTransferProgress

    return XbmcFileTransferProgress()


@singleton
def http_client():
    from util.httpclient import HttpClient

    return HttpClient(progress=file_transfer_progress())


def details_cache():
    return plugin.get_storage('details_cache.db', ttl=3 * 60 * 24)


def folders_cache():
    return plugin.get_storage('folders_cache.db', ttl=60 * 12)


def search_cache():
    return plugin.get_storage('search_cache.db', ttl=60)


@singleton
def scraper():
    from mediapoisk.scraper import MediaPoiskScraper

    return MediaPoiskScraper(http_client=http_client(),
                             http_params={'tries': 5},
                             max_workers=plugin.get_setting('batch-results', int),
                             details_cache=details_cache(),
                             folders_cache=folders_cache(),
                             search_cache=search_cache(),
                             persistent_ids=not_refreshing_items(),
                             timeout=30)


# noinspection PyShadowingBuiltins
def search_filter(section=None, format=None, people=None, studio=None, genres=None, countries=None, languages=None,
                  rating_min=None, rating_max=None, year_min=None, year_max=None, order_by=None, order_dir=None,
                  user_rating_min=None, user_rating_max=None, name=None, page_size=None):
    from mediapoisk.searchfilter import MediaPoiskSearchFilter

    page_size = page_size or plugin.get_setting('results-per-page', int)
    return MediaPoiskSearchFilter(section, format, people, studio, genres, countries, languages, rating_min,
                                  rating_max, year_min, year_max, order_by, order_dir, user_rating_min, user_rating_max,
                                  name, page_size)


@singleton
def transmission_client():
    from mediapoisk.torrent.client import TransmissionClient

    return TransmissionClient(login=plugin.get_setting('transmission-login', unicode),
                              password=plugin.get_setting('transmission-password', unicode),
                              host=plugin.get_setting('transmission-host', unicode),
                              port=plugin.get_setting('transmission-port', int, default=9091),
                              path=plugin.get_setting('transmission-path', unicode),
                              timeout=5)


@singleton
def utorrent_client():
    from mediapoisk.torrent.client import UTorrentClient

    return UTorrentClient(login=plugin.get_setting('utorrent-login', unicode),
                          password=plugin.get_setting('utorrent-password', unicode),
                          host=plugin.get_setting('utorrent-host', unicode),
                          port=plugin.get_setting('utorrent-port', int, default=8080),
                          timeout=5)


@singleton
def torrent_client():
    """
    :rtype : TorrentClient
    """
    client = plugin.get_setting('torrent-client', choices=(None, utorrent_client, transmission_client))
    return client() if client else None


@singleton
def acestream_engine():
    import acestream
    from mediapoisk.common import temp_path

    return acestream.Engine(host=plugin.get_setting('as-host', unicode),
                            port=plugin.get_setting('as-port', int, default=62062),
                            save_path=temp_path() if plugin.get_setting('save-files', int) else None)


@singleton
def stream_buffering_progress():
    from mediapoisk.xbmcstuff import XbmcTorrentTransferProgress

    return XbmcTorrentTransferProgress()


@singleton
def stream_playing_progress():
    from mediapoisk.xbmcstuff import XbmcOverlayTorrentTransferProgress

    return XbmcOverlayTorrentTransferProgress(window_id=12005)


@singleton
def ace_stream():
    from mediapoisk.torrent.stream import AceStream

    return AceStream(engine=acestream_engine(),
                     buffering_progress=stream_buffering_progress(),
                     playing_progress=stream_playing_progress())


@singleton
def torrent2http_engine():
    import torrent2http
    from mediapoisk.common import temp_path

    return torrent2http.Engine(download_path=temp_path(),
                               state_file=plugin.addon_data_path('t2h_state'),
                               connections_limit=plugin.get_setting('t2h-max-connections', int, default=None),
                               download_kbps=plugin.get_setting('t2h-download-rate', int, default=None),
                               upload_kbps=plugin.get_setting('t2h-upload-rate', int, default=None),
                               log_overall_progress=plugin.get_setting('t2h-debug-mode', bool),
                               log_pieces_progress=plugin.get_setting('t2h-debug-mode', bool),
                               debug_alerts=plugin.get_setting('t2h-debug-mode', bool),
                               listen_port=plugin.get_setting('t2h-listen-port', int, default=6881),
                               use_random_port=plugin.get_setting('t2h-use-random-port', bool),
                               trackers=['http://retracker.local/announce'],
                               keep_files=True,
                               enable_utp=False)


@singleton
def torrent2http_stream():
    from mediapoisk.torrent.stream import Torrent2HttpStream

    return Torrent2HttpStream(engine=torrent2http_engine(),
                              buffering_progress=stream_buffering_progress(),
                              playing_progress=stream_playing_progress(),
                              pre_buffer_bytes=plugin.get_setting('t2h-pre-buffer-mb', int) * 1024 * 1024)


@singleton
def torrent_stream():
    """
    :rtype : TorrentStream
    """
    stream = plugin.get_setting('torrent-stream', choices=(torrent2http_stream, ace_stream))
    return stream()


def torrent(url=None, data=None, file_name=None):
    from mediapoisk.torrent import Torrent

    return Torrent(url, data, file_name, http_client())


@singleton
def player():
    from mediapoisk.xbmcstuff import XbmcPlayer

    return XbmcPlayer()


@singleton
def watched_items():
    from mediapoisk.storage import WatchedItems

    return WatchedItems(plugin.get_storage('watched_items.db', cached=True))


@singleton
def bookmarks():
    from mediapoisk.storage import Bookmarks

    return Bookmarks(common_storage())


@singleton
def history():
    from mediapoisk.storage import HistoryItems

    return HistoryItems(common_storage(),
                        plugin.get_setting('history-items-count', int))


@singleton
def library_manager():
    from mediapoisk.library import LibraryManager

    return LibraryManager(plugin.get_setting('library-path', unicode),
                          plugin.get_storage('library_items.db', cached=True))


def common_storage():
    return plugin.get_storage('common.db', cached=True)


def search_storage():
    return common_storage()


def meta_cache():
    return plugin.get_storage('meta_cache.db', ttl=60, cached=True)


def not_refreshing_items():
    storage = common_storage()
    return storage.setdefault('not_refreshing_items', {})
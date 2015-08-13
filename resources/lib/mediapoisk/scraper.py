# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from collections import namedtuple
from mediapoisk.enumerations import *
from mediapoisk.common import LocalizedError, str_to_date
from util.timer import Timer
from util.htmldocument import HtmlDocument
from util.httpclient import HttpClient
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from mediapoisk.searchfilter import MediaPoiskSearchFilter

import re
import urllib
import urllib2
import logging
import socket


Media = namedtuple('Media', ['id', 'title', 'original_title', 'date', 'flag', 'quality', 'genres',
                             'languages', 'countries', 'year', 'rating', 'user_rating', 'section'])

Details = namedtuple('Details', ['title', 'original_title', 'countries', 'year', 'release_date', 'release_date_russia',
                                 'studios', 'genres', 'plot', 'creators', 'actors', 'voice_artists',
                                 'rating', 'user_rating', 'poster', 'media_id', 'section', 'screenshots'])

Folder = namedtuple('Folder', ['id', 'media_id', 'title', 'flag', 'link', 'quality', 'languages', 'fmt',
                               'embedded_subtitles', 'external_subtitles', 'size', 'files', 'section'])

File = namedtuple('File', ['id', 'media_id', 'folder_id', 'title', 'flag', 'link', 'file_format',
                           'duration', 'resolution', 'section'])

Quality = namedtuple('Quality', ['format', 'video', 'audio'])


class ScraperError(LocalizedError):
    pass


class AbstractScraper:
    def __init__(self, log=None, http_params=None, http_client=None, max_workers=10, timeout=30,
                 details_cache=None, folders_cache=None, search_cache=None, persistent_ids=None):
        self.log = log or logging.getLogger(__name__)
        self.http_client = http_client or HttpClient()
        self.http_params = http_params or {}
        self.timeout = timeout
        self.details_cache = details_cache if details_cache is not None else {}
        self.folders_cache = folders_cache if folders_cache is not None else {}
        self.search_cache = search_cache if search_cache is not None else {}
        self.max_workers = max_workers
        self.persistent_ids = persistent_ids or []
        self.http_response = None
        self.has_more = False

    def fetch_page(self, url, cookie_jar=None):
        try:
            self.http_client.cookie_jar = cookie_jar
            self.http_response = self.http_client.fetch(url, timeout=self.timeout, **self.http_params)
            return self.http_response.body
        except urllib2.URLError, e:
            if isinstance(e.reason, socket.timeout):
                raise ScraperError(32000, "Timeout while fetching URL: %s" % url, cause=e)
            else:
                raise ScraperError(32001, "Can't fetch URL: %s" % url, cause=e)

    def search(self, search_filter=None, skip=None):
        raise NotImplementedError()

    def get_details(self, section, media_id):
        raise NotImplementedError()

    def get_folders(self, section, media_id):
        raise NotImplementedError()

    def get_files(self, section, media_id, folder_id):
        raise NotImplementedError()

    def search_cached(self, search_filter=None, skip=None):
        key = hash((search_filter, skip))
        if key not in self.search_cache:
            self.search_cache[key] = (self.search(search_filter, skip), self.has_more)
        res, self.has_more = self.search_cache[key]
        return res

    def get_details_bulk(self, section, media_ids):
        """
        :rtype : dict[int, Details]
        """
        if not media_ids:
            return {}
        cached_details = self.details_cache.keys()
        not_cached_ids = [_id for _id in media_ids if _id not in cached_details]
        results = dict((_id, self.details_cache[_id]) for _id in media_ids if _id in cached_details)
        with Timer(logger=self.log, name="Bulk fetching"):
            try:
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    futures = [executor.submit(self.get_details, section, _id) for _id in not_cached_ids]
                    for future in as_completed(futures, self.timeout):
                        result = future.result()
                        _id = result.media_id
                        self.details_cache[_id] = results[_id] = result
                        if _id in self.persistent_ids:
                            self.details_cache.protect_item(_id)
            except TimeoutError as e:
                raise ScraperError(32000, "Timeout while fetching URLs", cause=e)
        return results

    def get_details_cached(self, section, media_id):
        """
        :rtype : Details
        """
        return self.get_details_bulk(section, [media_id])[media_id]

    def get_folders_bulk(self, section, media_ids):
        """
        :rtype : dict[int, list[Folder]]
        """
        if not media_ids:
            return {}
        cached_folders = self.folders_cache.keys()
        not_cached_ids = [_id for _id in media_ids if _id not in cached_folders]
        results = dict((_id, self.folders_cache[_id]) for _id in media_ids if _id in cached_folders)
        with Timer(logger=self.log, name="Bulk fetching"):
            try:
                with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                    folder_futures = dict((executor.submit(self.get_folders, section, _id), _id)
                                          for _id in not_cached_ids)
                    files_futures = {}
                    for future in as_completed(folder_futures, self.timeout):
                        result = future.result()
                        _id = folder_futures[future]
                        results[_id] = result
                        if len(result) > 1:
                            files_futures.update(dict((executor.submit(self.get_files, section, _id, f.id), (_id, i))
                                                      for i, f in enumerate(result)))
                        else:
                            self.folders_cache[_id] = result
                            if _id in self.persistent_ids:
                                self.folders_cache.protect_item(_id)

                    for future in as_completed(files_futures, self.timeout):
                        result = future.result()
                        _id, i = files_futures[future]
                        results[_id][i].files.extend(result)
                        self.folders_cache[_id] = results[_id]
                        if _id in self.persistent_ids:
                            self.folders_cache.protect_item(_id)
            except TimeoutError as e:
                raise ScraperError(32000, "Timeout while fetching URLs", cause=e)
        return results

    def get_folders_cached(self, section, media_id):
        """
        :rtype : list[Folder]
        """
        return self.get_folders_bulk(section, [media_id])[media_id]

    def get_folder_cached(self, section, media_id, folder_id):
        folders = self.get_folders_cached(section, media_id)
        return next((folder for folder in folders if folder.id == folder_id), None)

    def get_files_cached(self, section, media_id, folder_id):
        folder = self.get_folder_cached(section, media_id, folder_id)
        return folder and folder.files or []


class MediaPoiskScraper(AbstractScraper):
    base_url = "http://mediapoisk.info"

    def search(self, search_filter=None, skip=None):
        """
        Search media

        :type search_filter: MediaPoiskSearchFilter
        :param search_filter: Use SearchFilter
        :param skip: How many results to skip (for paging)
        """
        url = self.base_url + '/media_page.php'
        query = {}
        cookie_jar = None
        if search_filter:
            cookie_jar = search_filter.cookies
            query.update(search_filter.encoded_query)
            self.log.info('Using search filter: %s', search_filter)
        if skip:
            query['skip'] = skip
        if query:
            url += "?" + urllib.urlencode(query)

        with Timer(logger=self.log, name='Fetching URL'):
            html = self.fetch_page(url, cookie_jar=cookie_jar)

        section = search_filter.section
        results = []
        warnings = 0
        with Timer(logger=self.log, name='Parsing'):
            document = HtmlDocument.from_string(html)
            self.has_more = False
            table = document.find('table', {'class': 'zebra'})
            navbar = table.find('tr', {'class': 'navbar'}).first
            if "Ничего не найдено" in navbar.text:
                self.log.info("No results found.")
                return []

            cur_pages = navbar.find('b').text
            self.has_more = not navbar.text.endswith(cur_pages)
            rows = table.find('tr', {'class': 'even|odd'})
            for row in rows:
                try:
                    cols = row.find('td')

                    title_td = cols[2]
                    link = title_td.find('a').attr('href')
                    media_id = int(link.split('=')[-1])
                    title = title_td.find('span', {'class': 'title'}).text
                    original_title = title_td.find('span', {'class': 'subtitle'}).strings
                    year = cols[7].text
                    rating = cols[-2].text
                    rating = "%01.01f" % (float(rating))
                    if rating == '0.0':
                        rating = None
                    user_rating = cols[-1].text
                    user_rating = "%01.01f" % (float(user_rating))
                    if user_rating == '0.0':
                        user_rating = None

                    added_date = cols[1].find('span').attr('title').split(" ")[0]
                    added_date = str_to_date(added_date)

                    flag = Flag.find(cols[0].find('img').attr('title'))

                    qua_td = cols[3]
                    fmt_str = qua_td.find('img').attr('alt')
                    fmt = Format.find(fmt_str)
                    if not format:
                        self.log.warn('Unknown format: %s', fmt_str)
                        warnings += 1
                    qua_str = qua_td.find('span').attr('title').split(",")
                    video_qua_str = qua_str[0].split(": ")[1]
                    audio_qua_str = qua_str[1].split(": ")[1]

                    video_quality = VideoQuality.find(video_qua_str)
                    if not video_quality:
                        self.log.warn('Unknown video quality: %s', video_qua_str)
                        warnings += 1
                    audio_quality = AudioQuality.find(audio_qua_str)
                    if not audio_quality:
                        self.log.warn('Unknown audio quality: %s', audio_qua_str)
                        warnings += 1

                    quality = Quality(fmt, video_quality, audio_quality)

                    languages = []
                    for img in cols[4].find('img'):
                        name = img.attr('alt')
                        language = Language.find(name)
                        if not language:
                            self.log.warn('Unknown language: %s', name)
                            language = name
                            warnings += 1
                        languages.append(language)

                    genres = []
                    for a in cols[5].find('a'):
                        name = a.text
                        genre = Genre.find(name)
                        if not genre:
                            self.log.warn('Unknown genre: %s', name)
                            genre = name
                            warnings += 1
                        genres.append(genre)

                    countries = []
                    for a in cols[6].find('a'):
                        name = a.text
                        country = Country.find(name)
                        if not country:
                            self.log.warn('Unknown country: %s', name)
                            country = name
                            warnings += 1
                        countries.append(country)

                    media = Media(media_id, title, original_title, added_date, flag, quality, genres, languages,
                                  countries, year, rating, user_rating, section)

                    self.log.debug(repr(media).decode("unicode-escape"))
                    results.append(media)
                except Exception as e:
                    self.log.exception(e)
                    warnings += 1

            self.log.info("Found %d result(s), %d warning(s).", len(results), warnings)

        return results

    def _parse_details(self, html, section, media_id):
        details = None
        warnings = 0
        with Timer(logger=self.log, name='Parsing'):
            document = HtmlDocument.from_string(html)
            contents = document.find('td', {'class': 'contents'})
            info_bar = contents.find('table', {'class': 'infobar'})
            if not info_bar:
                raise ScraperError(32003, "No media found with ID %d" % media_id)
            info_cols = info_bar.find('td')

            title = info_cols[0].find('span', {'class': 'title'}).text
            original_title = info_cols[0].find('span', {'class': 'subtitle'}).strings

            genres = []
            for name in info_cols[1].before_text.split(", "):
                genre = Genre.find(name)
                if not genre:
                    self.log.warn('Unknown genre: %s', name)
                    genre = name
                    warnings += 1
                genres.append(genre)

            countries = []
            temp_list = info_cols[1].after_text.split(", ")
            for name in temp_list[:-1]:
                country = Country.find(name)
                if not country:
                    self.log.warn('Unknown country: %s', name)
                    country = name
                    warnings += 1
                countries.append(country)

            year = temp_list[-1]

            studios = []
            creators = []
            actors = []
            voice_artists = []
            release_date = release_date_russia = rating = user_rating = None

            user_rating_re = re.search('(\d+\.\d+)', info_cols[2].before_text)
            if user_rating_re:
                user_rating = user_rating_re.group(0)
            rating_re = re.search('(\d+\.\d+)', info_cols[2].after_text)
            if rating_re:
                rating = rating_re.group(0)

            properties = contents.find('p', {'class': 'property'})

            for prop in properties:
                try:
                    label = prop.before_text
                    value = prop.find('span')

                    if label == 'Дата премьеры:':
                        release_date = value.text
                    elif label == 'Дата российской премьеры:':
                        release_date_russia = value.text
                    elif label == 'Студия:':
                        studios = [item.text for item in value.find('a')]
                    elif label == 'Создатели:':
                        creators = value.find('a').strings
                    elif label == 'В ролях:':
                        actors = value.find('a').strings
                    elif label == 'Роли озвучивали:':
                        voice_artists = value.find('a').strings
                    elif label == 'Серии:':
                        pass
                    else:
                        self.log.warn('Unknown description block: %s', label)
                        warnings += 1
                except Exception as e:
                    self.log.exception(e)
                    warnings += 1

            plot = contents.find('div', {'style': 'display:table-cell;.*?'}).text
            poster = contents.find("div", {'class': 'media_pic'}).find("a").attr('href')
            screenshots = contents.find('div', {'id': 'imgsContainer'}).find('a').attrs('href')

            details = Details(title, original_title, countries, year, release_date, release_date_russia,
                              studios, genres, plot, creators, actors, voice_artists,
                              rating, user_rating, poster, media_id, section, screenshots)
        self.log.info("Got details successfully, %d warning(s)." % warnings)
        self.log.debug(repr(details).decode("unicode-escape"))

        return details

    def get_details(self, section, media_id):
        """
        Get media details by media ID

        :param section: Section
        :param media_id: Media ID
        """
        url = "%s/media_show_page.php?section=%s&id=%d" % (self.base_url, section.filter_val, media_id)

        with Timer(logger=self.log, name='Fetching URL'):
            html = self.fetch_page(url)

        return self._parse_details(html, section, media_id)

    def get_folders(self, section, media_id):
        """
        Get media folders by media ID

        :param section: Section
        :param media_id: Media ID
        """
        url = "%s/media_show_page.php?section=%s&id=%d" % (self.base_url, section.filter_val, media_id)

        with Timer(logger=self.log, name='Fetching URL'):
            html = self.fetch_page(url)
        folders = []
        warnings = 0
        with Timer(logger=self.log, name='Parsing folders'):
            document = HtmlDocument.from_string(html)
            copies_table = document.find('table', {'class': 'copies'})
            copies = copies_table.find("table", {'class': 'copy'})
            if not copies:
                self.log.warn("No folders found.")
                return []
            for c in copies:
                try:
                    folder_id = int(c.attr('id')[4:])
                    title_td = c.find("td", {'class': 'copy_title'})
                    icons = title_td.find('img')
                    flag = fmt = None
                    for alt in icons.attrs('alt'):
                        f = Flag.find(alt)
                        if f:
                            flag = f
                        f = Format.find(alt)
                        if f:
                            fmt = f
                    title = title_td.text
                    server_td = c.find("td", {'class': 'server'})
                    link = server_td.find("a", {'href': '/playlist\.php.*?'}).attr('href')
                    if link:
                        # noinspection PyAugmentAssignment
                        link = self.base_url + link
                    else:
                        self.log.warn('Torrent link is undefined')
                        warnings += 1
                    br_td = c.find("td", {'class': 'br'})
                    languages = None
                    video_quality = audio_quality = None
                    embedded_subtitles = external_subtitles = None
                    size = 0
                    for p in br_td.find('p'):
                        name, val = (p.before_text.split(":", 2) + [""])[:2]
                        val = val.lstrip()
                        if name == 'Язык':
                            languages = []
                            for lang in p.find('img', {'class': 'flag'}).attrs('alt'):
                                language = Language.find(lang)
                                if not language:
                                    self.log.warn('Unknown audio language: %s', lang)
                                    language = lang
                                    warnings += 1
                                languages.append(language)
                        elif name == 'Качество звука':
                            audio_quality = AudioQuality.find(val)
                            if not audio_quality:
                                self.log.warn('Unknown audio quality: %s', val)
                                audio_quality = val
                                warnings += 1
                        elif name == 'Качество изображения':
                            video_quality = VideoQuality.find(val)
                            if not video_quality:
                                self.log.warn('Unknown video quality: %s', val)
                                video_quality = val
                                warnings += 1
                        elif name == 'Встроенные субтитры':
                            embedded_subtitles = []
                            for lang in p.find('img', {'class': 'flag'}).attrs('alt'):
                                language = Language.find(lang)
                                if not language:
                                    self.log.warn('Unknown embedded subtitles language: %s', lang)
                                    language = lang
                                    warnings += 1
                                embedded_subtitles.append(language)
                        elif name == 'Внешние или отключаемые субтитры':
                            external_subtitles = []
                            for lang in p.find('img', {'class': 'flag'}).attrs('alt'):
                                language = Language.find(lang)
                                if not language:
                                    self.log.warn('Unknown external subtitles language: %s', lang)
                                    language = lang
                                    warnings += 1
                                external_subtitles.append(language)
                        elif name == 'Размер файлов':
                            size = self._parse_size(val)
                            if size is None:
                                self.log.warn("Can't parse size: %s", val)
                                warnings += 1
                        else:
                            self.log.warn("Unknown folder property: %s", name)
                            warnings += 1

                    quality = Quality(fmt, video_quality, audio_quality)
                    files = self._parse_files(copies_table, section, media_id, folder_id)
                    folder = Folder(folder_id, media_id, title, flag, link, quality, languages, fmt,
                                    embedded_subtitles, external_subtitles, size, files, section)
                    self.log.debug(repr(folder).decode("unicode-escape"))
                    folders.append(folder)
                except Exception as e:
                    self.log.exception(e)
                    warnings += 1

            self.log.info("Got %d folder(s) successfully, %d warning(s)." % (len(folders), warnings))
        return folders

    def get_files(self, section, media_id, folder_id):
        """
        Get media files by folder ID

        :param section: Section
        :param media_id: Media ID
        :param folder_id: Folder ID
        """
        url = "%s/media_show_page.php?section=%s&id=%d&cid=%d" % (self.base_url, section.filter_val,
                                                                  media_id, folder_id)

        with Timer(logger=self.log, name='Fetching URL'):
            html = self.fetch_page(url)

        document = HtmlDocument.from_string(html)
        return self._parse_files(document, section, media_id, folder_id)

    def _parse_files(self, doc, section, media_id, folder_id):
        files = []
        warnings = 0
        with Timer(logger=self.log, name='Parsing files'):
            files_tr = doc.find('tr', {'class': 'files'})
            rows = files_tr.find('tr')[1:]
            if not rows:
                self.log.warn("No files found.")
                return []
            for row in rows:
                try:
                    cols = row.find('td')
                    icon_class = cols[0].find('img').attr('alt')
                    flag = Flag.find(icon_class)
                    link = cols[1].find('a', {'href': '/playlist\.php.*?'}).attr('href')
                    if not link:
                        self.log.warn("No link to torrent file found, skipping...")
                        warnings += 1
                        continue
                    file_id = re.search(r'fid=(\d+)', link)
                    if not file_id:
                        self.log.warn("Invalid torrent link: %s", link)
                        warnings += 1
                        continue
                    file_id = file_id.group(1)
                    # noinspection PyAugmentAssignment
                    link = self.base_url + link
                    title = cols[2].text
                    file_fmt = cols[5].text
                    duration = self._parse_duration(cols[4].text) if cols[4].text else 0
                    resolution = cols[6].text.split('x') if cols[6].text else [0, 0]
                    f = File(file_id, media_id, folder_id, title, flag, link, file_fmt,
                             duration, resolution, section)
                    self.log.debug(repr(f).decode("unicode-escape"))
                    files.append(f)
                except Exception as e:
                    self.log.exception(e)
                    warnings += 1
        self.log.info("Got %d file(s) successfully, %d warning(s)." % (len(files), warnings))
        return files

    @staticmethod
    def _parse_size(size):
        size = size.strip(" \t\xa0")
        if size.isdigit():
            return long(size)
        else:
            num, qua = size[:-2].rstrip(), size[-2:].lower()
            if qua == 'mb' or qua == 'мб':
                return long(float(num)*1024*1024)
            elif qua == 'gb' or qua == 'гб':
                return long(float(num)*1024*1024*1024)
            elif qua == 'tb' or qua == 'тб':
                return long(float(num)*1024*1024*1024*1024)

    @staticmethod
    def _parse_duration(duration):
        duration = duration.strip(" \t\xa0")
        parts = duration.split(":")
        if len(parts) == 1:
            return int(duration)
        elif len(parts) == 2:
            return int(parts[0])*60+int(parts[1])
        elif len(parts) == 3:
            return int(parts[0])*3600+int(parts[1])*60+int(parts[2])
        elif len(parts) == 4:
            return int(parts[0])*86400+int(parts[1])*3600+int(parts[2])*60+int(parts[3])

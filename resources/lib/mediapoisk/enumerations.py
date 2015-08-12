# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from mediapoisk.common import LocalizedEnum
from copy import copy

try:
    from collections import OrderedDict
except ImportError:
    from util.ordereddict import OrderedDict


class Attribute(LocalizedEnum):
    def get_lang_base(self):
        raise NotImplementedError()

    @property
    def lang_id(self):
        return self.get_lang_base() + self.id

    @property
    def id(self):
        return self.value[0]

    @property
    def filter_val(self):
        return self.value[1]

    def __repr__(self):
        return "<%s.%s>" % (self.__class__.__name__, self._name_)

    @classmethod
    def find(cls, what):
        for i in cls.__iter__():
            if what in i.value or i.name == what:
                return i
        return None

    @classmethod
    def all(cls):
        return [g for g in cls if g.id > 0]


class Order(Attribute):
    RATING = (1, 'rating')
    USER_RATING = (2, 'user_rating')
    YEAR = (3, 'year')
    NAME = (4, 'title')
    DATE = (5, 'entry_date')
    GENRE = (6, 'genre')
    COUNTRY = (7, 'country')

    def get_lang_base(self):
        return 30280


class OrderDirection(Attribute):
    ASC = (1, 'asc')
    DESC = (2, 'desc')

    def get_lang_base(self):
        return 30290


class Section(Attribute):
    MOVIES = (10, 'video', 'Movies')
    SERIES = (20, 'series', 'Series')
    ANIME = (30, 'anime', 'Anime')

    # noinspection PyUnusedLocal
    def __init__(self, *args):
        self.lang_base = 31000

    def get_lang_base(self):
        return self.lang_base

    @property
    def singular(self):
        c = copy(self)
        c.lang_base = 31040
        return c

    @property
    def folder_name(self):
        return self.value[2]

    def is_series(self):
        return self in [Section.SERIES, Section.ANIME]


class Format(Attribute):
    AVI = (10, "AVI")
    HD = (20, "HD-rip")
    HD1080 = (30, "HD-rip 1080")

    def get_lang_base(self):
        return 30900

    @property
    def width(self):
        return FORMAT_DIMENSIONS[self][0]

    @property
    def height(self):
        return FORMAT_DIMENSIONS[self][1]


FORMAT_DIMENSIONS = {
    Format.AVI: (720, 480),
    Format.HD: (1280, 720),
    Format.HD1080: (1920, 1080),
}


class Genre(Attribute):
    BIOGRAPHY = (1, "Биографический")
    ACTION = (2, "Боевик")
    WESTERN = (3, "Вестерн")
    MILITARY = (4, "Военный")
    DETECTIVE = (5, "Детектив")
    CHILDREN = (6, "Детский")
    DOCUMENTARY = (7, "Документальный")
    DRAMA = (8, "Драма")
    HISTORICAL = (9, "Исторический")
    CATASTROPHE = (10, "Катастрофа")
    STORY = (11, "Киноповесть")
    COMEDY = (12, "Комедия")
    SHORT = (13, "Короткометражный")
    CRIMINAL = (14, "Криминал")
    ROMANCE = (15, "Мелодрама")
    MYSTIC = (16, "Мистика")
    MUSIC = (17, "Музыкальный")
    CARTOON = (18, "Мультфильм")
    ADULT_CARTOON = (19, "Мультфильм для взрослых")
    OPERA = (20, "Опера")
    ADVENTURES = (21, "Приключения")
    PROGRAM = (22, "Программа")
    PSYCHOLOGICAL = (23, "Психологический")
    FAMILY = (24, "Семейный")
    TALE = (25, "Сказка")
    PLAY = (26, "Спектакль")
    SPORT = (27, "Спорт")
    THRILLER = (28, "Триллер")
    HORROR = (29, "Ужасы")
    EDUCATIONAL = (30, "Учебное пособие")
    FICTION = (31, "Фантастика")
    FANTASY = (32, "Фэнтази")
    EROTIC = (33, "Эротика")
    HUMOR = (34, "Юмор")

    def get_lang_base(self):
        return 30700


class Country(Attribute):
    AUSTRALIA = (1, "Австралия")
    GREAT_BRITAIN = (2, "Великобритания")
    GERMANY = (3, "Германия")
    HONGKONG = (4, "Гонконг")
    WESTERN_GERMANY = (5, "Западная Германия")
    INDIA = (6, "Индия")
    SPAIN = (7, "Испания")
    ITALY = (8, "Италия")
    CANADA = (9, "Канада")
    CHINA = (10, "Китай")
    MEXICO = (11, "Мексика")
    NETHERLANDS = (12, "Нидерланды")
    POLAND = (13, "Польша")
    RUSSIA = (14, "Россия")
    USSR = (15, "СССР")
    USA = (16, "США")
    FRANCE = (17, "Франция")
    SWEDEN = (18, "Швеция")
    SOUTH_KOREA = (19, "Южная Корея")
    JAPAN = (20, "Япония")
    GEORGIA = (21, "Грузия")
    ESTONIA = (22, "Эстония")
    DENMARK = (23, "Дания")
    BRAZIL = (24, "Бразилия")
    NORWAY = (25, "Норвегия")
    IRELAND = (26, "Ирландия")
    INDONESIA = (27, "Индонезия")
    THAILAND = (28, "Тайланд")
    YUGOSLAVIA = (29, "Югославия")
    ISRAEL = (30, "Израиль")
    FINLAND = (31, "Финляндия")
    UKRAINE = (32, "Украина")
    BULGARIA = (33, "Болгария")
    SWITZERLAND = (34, "Швейцария")
    NEW_ZEALAND = (35, "Новая Зеландия")
    AZERBAIJAN = (36, "Азербайджан")
    CZECH_REPUBLIC = (37, "Чехия")
    UAE = (38, "Объединенные Арабские Эмираты")
    SOUTH_AFRICA = (39, "Южная Африка")
    AUSTRIA = (40, "Австрия")
    BELARUS = (41, "Беларусь")
    EGYPT = (42, "Египет")
    LUXEMBOURG = (43, "Люксембург")
    BELGIUM = (44, "Бельгия")
    TURKEY = (45, "Турция")
    GREECE = (46, "Греция")
    ARUBA = (47, "Аруба")
    SINGAPORE = (48, "Сингапур")
    TAIWAN = (49, "Тайвань")
    MALTA = (50, "Мальта")
    ARGENTINA = (51, "Аргентина")
    ROMANIA = (52, "Румыния")
    PERU = (53, "Перу")
    LATVIA = (54, "Латвия")
    BAHAMAS = (55, "Багамы")
    KAZAKHSTAN = (56, "Казахстан")
    VENEZUELA = (57, "Венесуэла")
    ICELAND = (58, "Исландия")
    MACEDONIA = (59, "Республика Македония")
    SLOVENIA = (60, "Словения")
    SERBIA = (61, "Сербия")
    CROATIA = (62, "Хорватия")
    MONTENEGRO = (63, "Черногория")
    FIJI = (64, "Фиджи")
    EASTERN_GERMANY = (65, "Восточная Германия")
    PHILIPPINES = (66, "Филиппины")
    CHILE = (67, "Чили")
    MONGOLIA = (68, "Монголия")
    CZECHOSLOVAKIA = (69, "Чехословакия")
    HUNGARY = (70, "Венгрия")

    def get_lang_base(self):
        return 30500


class Language(Attribute):
    RUSSIAN = (10, "Русский")
    ENGLISH = (11, "Английский")
    JAPANESE = (12, "Японский")
    CHINESE = (13, "Китайский")
    GERMAN = (14, "Немецкий")
    FRENCH = (15, "Французский")
    ITALIAN = (16, "Итальянский")
    SPANISH = (17, "Испанский")
    KOREAN = (18, "Корейский")
    GOBLIN = (19, "Перевод Гоблина")
    HUNGARIAN = (20, "Венгерский")
    SWEDISH = (21, "Шведский")
    EUROPEAN = (22, "Европейские языки")
    WITHOUT_SPEECH = (23, "Без речи")
    GEORGIAN = (24, "Грузинский")
    ESTONIAN = (25, "Эстонский")
    DANISH = (26, "Датский")
    NORWEGIAN = (27, "Норвежский")
    INDONESIAN = (28, "Индонезийский")
    THAI = (29, "Тайский")
    HINDI = (30, "Хинди")
    SERBIAN = (31, "Сербский")
    POLISH = (32, "Польский")
    HEBREW = (33, "Иврит")
    UKRAINIAN = (34, "Украинский")
    DUTCH = (35, "Нидерландский")
    TURKISH = (36, "Турецкий")
    MALAYALAM = (37, "Малаялам")
    LITHUANIAN = (38, "Литовский")
    BENGALI = (39, "Бенгали")
    PORTUGUESE = (40, "Португальский")
    BENGAL = (41, "Бенгальский")
    LATVIAN = (42, "Латышский")
    BULGARIAN = (43, "Болгарский")
    TELUGU = (44, "Телугу")
    ICELANDIC = (45, "Исландский")
    MACEDONIAN = (46, "Македонский")
    FARSI = (47, "Фарси")
    MONGOLIAN = (48, "Монгольский")
    CZECH = (49, "Чешский")
    TAIWANESE = (50, "Тайваньский")

    def get_lang_base(self):
        return 30400


class AudioQuality(Attribute):
    WITHOUT_TRANSLATION = (12, "нет перевода")
    CAM_RIP = (11, "(1) дубляж с экранки")
    VOLODARSKY = (10, "(1) озвучка секты им. Л.В. Володарского")
    ONE_VOICE = (20, "(2) любительский одноголосый перевод")
    MANY_VOICES = (30, "(3) любительский многоголосый перевод")
    LINE = (31, "(3) звук line")
    PROFESSIONAL = (40, "(4) профессиональный перевод")
    ORIGINAL = (50, "(5) оригинальная дорожка/полный дубляж")

    def get_lang_base(self):
        return 30300

    def __nonzero__(self):
        return self.value[0] > 0


class VideoQuality(Attribute):
    BAD_CAM_RIP = (10, "(1) плохая экранка")
    CAM_RIP = (20, "(2) экранка")
    VHS_RIP = (21, "(2) VHS-рип")
    TV_RIP = (30, "(3) TV-рип")
    DVD_SCR = (31, "(3) DVDscr")
    HDTV = (32, "(3) HDTV")
    HDTV_HD = (33, "(3) HDTV HD")
    DVD_RIP = (40, "(4) DVD-рип")
    WEB_DL = (41, "(4) Web-DL")
    HD_RIP = (50, "(5) HD-рип")
    WEB_DL_HD = (51, "(5) Web-DL HD")

    def get_lang_base(self):
        return 30100

    def __nonzero__(self):
        return self.value[0] > 0


class Flag(Attribute):
    QUALITY_UPDATED = (1, "новое качество")
    RECENTLY_ADDED = (2, "новинка")
    NEW_SERIES = (3, "новые серии")

    def get_lang_base(self):
        return 30200

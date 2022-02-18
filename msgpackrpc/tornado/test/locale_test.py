from __future__ import absolute_import, division, print_function

import datetime
import os
import shutil
import tempfile

import msgpackrpc.tornado.locale
from msgpackrpc.tornado.escape import utf8, to_unicode
from msgpackrpc.tornado.test.util import unittest, skipOnAppEngine
from msgpackrpc.tornado.util import unicode_type


class TranslationLoaderTest(unittest.TestCase):
    # TODO: less hacky way to get isolated tests
    SAVE_VARS = ['_translations', '_supported_locales', '_use_gettext']

    def clear_locale_cache(self):
        if hasattr(msgpackrpc.tornado.locale.Locale, '_cache'):
            del msgpackrpc.tornado.locale.Locale._cache

    def setUp(self):
        self.saved = {}
        for var in TranslationLoaderTest.SAVE_VARS:
            self.saved[var] = getattr(msgpackrpc.tornado.locale, var)
        self.clear_locale_cache()

    def tearDown(self):
        for k, v in self.saved.items():
            setattr(msgpackrpc.tornado.locale, k, v)
        self.clear_locale_cache()

    def test_csv(self):
        msgpackrpc.tornado.locale.load_translations(
            os.path.join(os.path.dirname(__file__), 'csv_translations'))
        locale = msgpackrpc.tornado.locale.get("fr_FR")
        self.assertTrue(isinstance(locale, msgpackrpc.tornado.locale.CSVLocale))
        self.assertEqual(locale.translate("school"), u"\u00e9cole")

    # tempfile.mkdtemp is not available on app engine.
    @skipOnAppEngine
    def test_csv_bom(self):
        with open(os.path.join(os.path.dirname(__file__), 'csv_translations',
                               'fr_FR.csv'), 'rb') as f:
            char_data = to_unicode(f.read())
        # Re-encode our input data (which is utf-8 without BOM) in
        # encodings that use the BOM and ensure that we can still load
        # it. Note that utf-16-le and utf-16-be do not write a BOM,
        # so we only test whichver variant is native to our platform.
        for encoding in ['utf-8-sig', 'utf-16']:
            tmpdir = tempfile.mkdtemp()
            try:
                with open(os.path.join(tmpdir, 'fr_FR.csv'), 'wb') as f:
                    f.write(char_data.encode(encoding))
                msgpackrpc.tornado.locale.load_translations(tmpdir)
                locale = msgpackrpc.tornado.locale.get('fr_FR')
                self.assertIsInstance(locale, msgpackrpc.tornado.locale.CSVLocale)
                self.assertEqual(locale.translate("school"), u"\u00e9cole")
            finally:
                shutil.rmtree(tmpdir)

    def test_gettext(self):
        msgpackrpc.tornado.locale.load_gettext_translations(
            os.path.join(os.path.dirname(__file__), 'gettext_translations'),
            "tornado_test")
        locale = msgpackrpc.tornado.locale.get("fr_FR")
        self.assertTrue(isinstance(locale, msgpackrpc.tornado.locale.GettextLocale))
        self.assertEqual(locale.translate("school"), u"\u00e9cole")
        self.assertEqual(locale.pgettext("law", "right"), u"le droit")
        self.assertEqual(locale.pgettext("good", "right"), u"le bien")
        self.assertEqual(locale.pgettext("organization", "club", "clubs", 1), u"le club")
        self.assertEqual(locale.pgettext("organization", "club", "clubs", 2), u"les clubs")
        self.assertEqual(locale.pgettext("stick", "club", "clubs", 1), u"le b\xe2ton")
        self.assertEqual(locale.pgettext("stick", "club", "clubs", 2), u"les b\xe2tons")


class LocaleDataTest(unittest.TestCase):
    def test_non_ascii_name(self):
        name = msgpackrpc.tornado.locale.LOCALE_NAMES['es_LA']['name']
        self.assertTrue(isinstance(name, unicode_type))
        self.assertEqual(name, u'Espa\u00f1ol')
        self.assertEqual(utf8(name), b'Espa\xc3\xb1ol')


class EnglishTest(unittest.TestCase):
    def test_format_date(self):
        locale = msgpackrpc.tornado.locale.get('en_US')
        date = datetime.datetime(2013, 4, 28, 18, 35)
        self.assertEqual(locale.format_date(date, full_format=True),
                         'April 28, 2013 at 6:35 pm')

        self.assertEqual(locale.format_date(datetime.datetime.utcnow() - datetime.timedelta(seconds=2), full_format=False),
                         '2 seconds ago')
        self.assertEqual(locale.format_date(datetime.datetime.utcnow() - datetime.timedelta(minutes=2), full_format=False),
                         '2 minutes ago')
        self.assertEqual(locale.format_date(datetime.datetime.utcnow() - datetime.timedelta(hours=2), full_format=False),
                         '2 hours ago')

        now = datetime.datetime.utcnow()
        self.assertEqual(locale.format_date(now - datetime.timedelta(days=1), full_format=False, shorter=True),
                         'yesterday')

        date = now - datetime.timedelta(days=2)
        self.assertEqual(locale.format_date(date, full_format=False, shorter=True),
                         locale._weekdays[date.weekday()])

        date = now - datetime.timedelta(days=300)
        self.assertEqual(locale.format_date(date, full_format=False, shorter=True),
                         '%s %d' % (locale._months[date.month - 1], date.day))

        date = now - datetime.timedelta(days=500)
        self.assertEqual(locale.format_date(date, full_format=False, shorter=True),
                         '%s %d, %d' % (locale._months[date.month - 1], date.day, date.year))

    def test_friendly_number(self):
        locale = msgpackrpc.tornado.locale.get('en_US')
        self.assertEqual(locale.friendly_number(1000000), '1,000,000')

    def test_list(self):
        locale = msgpackrpc.tornado.locale.get('en_US')
        self.assertEqual(locale.list([]), '')
        self.assertEqual(locale.list(['A']), 'A')
        self.assertEqual(locale.list(['A', 'B']), 'A and B')
        self.assertEqual(locale.list(['A', 'B', 'C']), 'A, B and C')

    def test_format_day(self):
        locale = msgpackrpc.tornado.locale.get('en_US')
        date = datetime.datetime(2013, 4, 28, 18, 35)
        self.assertEqual(locale.format_day(date=date, dow=True), 'Sunday, April 28')
        self.assertEqual(locale.format_day(date=date, dow=False), 'April 28')

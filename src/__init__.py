#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import requests
import os
import shutil
from PIL import Image
import zipfile
from collections import namedtuple


TITLE_SIGNATURE = u'MARUMARU - 마루마루 - '
COOKIE_SIGNATURE = 'if(document.cookie.indexOf(\'sucuri_uidc='
COOKIE_NAME = 'sucuri_uidc'
CUSTOM_USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 \
(KHTML, like Gecko) Chrome/40.0.2214.91 Safari/537.36'


def __get_title(entry_page_tree):
    '''[Internal]'''
    return entry_page_tree.find('title').get_text()[len(TITLE_SIGNATURE):]


def __get_chapters(entry_page_tree):
    '''[Internal]'''
    chapters = []
    Chapter = namedtuple('Chapter', ['url', 'name'])
    for a in entry_page_tree.find(id='vContent').find_all('a')[1:]:
        url = a['href']
        name = a.get_text(strip=True)
        if 'http://www.mangaumaru.com/archives/' in url and name:
            chapters.append(Chapter(url, name))
    return chapters


def __make_output_dir(output, title):
    '''[Internal]'''
    if not os.path.exists(output):
        os.mkdir(output)
    path = os.path.join(output, title)
    if not os.path.exists(path):
        os.mkdir(path)
    return os.path.abspath(path)


def __resolve_js_block(session, chapter_url):
    '''[Internal]'''
    domain = chapter_url.split('/')[2]
    path = chapter_url.split('/')[3]
    r = session.get(chapter_url)
    if COOKIE_SIGNATURE in r.text:
        idx = r.text.find(COOKIE_SIGNATURE) + len(COOKIE_SIGNATURE)
        value = r.text[idx:r.text.find('\'', idx)]
        session.cookies.set(
            COOKIE_NAME,
            value,
            domain=domain,
            path='/' + path)
        session.headers.update({'Referer': chapter_url})


def __check_already_downloaded(zipfile_path):
    '''[Internal]'''
    if os.path.exists(zipfile_path):
        print('%s is already downloaded' % (zipfile_path))
        return True
    return False


def __save_chapter(session, chapter, output):
    '''[Internal]'''
    working_dir = os.path.join(output, chapter.name)
    zipfile_path = working_dir + '.zip'

    if __check_already_downloaded(zipfile_path):
        return

    __resolve_js_block(session, chapter.url)

    zf = zipfile.ZipFile(zipfile_path, 'w')
    os.mkdir(working_dir)
    os.chdir(working_dir)

    soup = BeautifulSoup(session.get(chapter.url).text)
    img_list = soup.find('p').find_all('a') or soup.find('p').find_all('img')

    cnt = 1
    for img in img_list:
        if 'href' in img.attrs:
            img_url = img.attrs['href']
        elif 'data-lazy-src' in img.attrs:
            img_url = img.attrs['data-lazy-src']
        else:
            img_url = img.attrs['src']
        try:
            from io import BytesIO
            i = Image.open(BytesIO(session.get(img_url).content))
        except:
            from StringIO import StringIO
            i = Image.open(StringIO(session.get(img_url).content))
        filename = '%d.jpg' % (cnt)
        i.save(filename)
        zf.write(filename)
        cnt += 1
    zf.close()
    shutil.rmtree(working_dir)


def download(url, output='./output'):
    """Download comic file from marumaru entry url

    :param url: URL of title's entry page
    'param output: Output directory

    Usage::

        >>> from marumaru-downloader import download
        >>> download('http://marumaru.in/b/manga/67808',
        >>>          './output')
    """
    s = requests.Session()
    s.headers.update({'User-Agent': CUSTOM_USER_AGENT})

    entry_page_tree = BeautifulSoup(s.get(url).text)
    output_dir_path = __make_output_dir(output, __get_title(entry_page_tree))
    for chapter in __get_chapters(entry_page_tree):
        __save_chapter(s, chapter, output_dir_path)


if __name__ == '__main__':
    import sys
    url = 'http://marumaru.in/b/manga/67808'
    if len(sys.argv) > 1:
        url = sys.argv[1]
    download(url)

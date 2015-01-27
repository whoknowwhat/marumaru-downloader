#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import requests
import os
import shutil
from PIL import Image
from io import BytesIO
import zipfile


TITLE_SIGNATURE = 'MARUMARU - 마루마루 - '
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
    for center in entry_page_tree.find(id='vContent').find_all('center')[1:]:
        for a in center.find_all('a'):
            chapters.append((a['href'], a.get_text()))
    return chapters


def __make_output_dir(output, title):
    '''[Internal]'''
    if not os.path.exists(output):
        os.mkdir(output)
    path = os.path.join(output, title)
    if not os.path.exists(path):
        os.mkdir(path)
    return os.path.abspath(path)


def __save_chapter(session, chapter, output):
    '''[Internal]'''
    working_dir = os.path.join(output, chapter[1])
    chapter_zip = working_dir + '.zip'
    if os.path.exists(chapter_zip):
        print('%s is already downloaded' % (chapter_zip))
        return

    domain = chapter[0].split('/')[2]
    path = chapter[0].split('/')[3]
    r = session.get(chapter[0])
    if COOKIE_SIGNATURE in r.text:
        idx = r.text.find(COOKIE_SIGNATURE) + len(COOKIE_SIGNATURE)
        value = r.text[idx:r.text.find('\'', idx)]
        session.cookies.set(
            COOKIE_NAME,
            value,
            domain=domain,
            path='/' + path)
        session.headers.update({'Referer': chapter[0]})

    zf = zipfile.ZipFile(chapter_zip, 'w')
    os.mkdir(working_dir)
    os.chdir(working_dir)
    cnt = 1

    soup = BeautifulSoup(session.get(chapter[0]).text)
    for a in soup.find('p').find_all('a'):
        i = Image.open(BytesIO(session.get(a['href']).content))
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
    download('http://marumaru.in/b/manga/67808')

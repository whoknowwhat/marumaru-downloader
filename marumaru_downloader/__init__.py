#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import requests
import os
import shutil
from PIL import Image
import zipfile
from collections import namedtuple
import re
import logging
from io import BytesIO
import time


logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())


__title__ = 'marumaru-downloader'
__version__ = '0.1.3'
__build__ = 0x000103
__author__ = 'eM'


TITLE_SIGNATURE = u'MARUMARU - 마루마루 - '
COOKIE_SIGNATURE = 'if(document.cookie.indexOf(\'sucuri_uidc='
COOKIE_NAME = 'sucuri_uidc'
CUSTOM_USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 \
(KHTML, like Gecko) Chrome/40.0.2214.91 Safari/537.36'


def __get_title(entry_page_tree):
    '''[Internal]'''
    return entry_page_tree.find('title').get_text()[len(TITLE_SIGNATURE):]


def __get_chapters(entry_page_tree, title):
    '''[Internal]'''
    chapters = []
    pattern = re.compile(u'^[0-9]+화$')
    Chapter = namedtuple('Chapter', ['url', 'name'])
    l = entry_page_tree.find(id='vContent').find_all('a')
    if l[0].find('img') != None:
        l = l[1:]
    for a in l:
        url = a['href']
        name = a.get_text(strip=True)
        if ('http://www.mangaumaru.com/archives/' in url or 'http://www.umaumaru.com/archives/' in url) and name:
            if pattern.match(name):
                name = '%s %s' % (title, name)
            chapters.append(Chapter(url, name))
    return chapters


def __make_output_dir(output, title):
    '''[Internal]'''
    if not os.path.exists(output):
        os.mkdir(output)
    title = title.replace(':', '-colon-').replace('?', '-question-').replace('/', '')
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
        logger.warning('%s is already downloaded' % (zipfile_path))
        return True
    return False


def __save_chapter(session, title, chapter, output):
    '''[Internal]'''
    working_dir = os.path.join(output, chapter.name.replace(':', '-colon-').replace('?', '-question-').replace('/', ''))
    zipfile_path = working_dir + '.zip'

    if __check_already_downloaded(zipfile_path):
        return

    # bypass javascript enable check
    __resolve_js_block(session, chapter.url)

    # create zipfile
    logger.warning('Start archiving [%s] >>' % (zipfile_path))
    zf = zipfile.ZipFile(zipfile_path, 'w')
    os.mkdir(working_dir)
    os.chdir(working_dir)

    # get image elements
    while True:
        try:
            soup = BeautifulSoup(session.get(chapter.url).text)
            img_list = soup.find('p').find_all('a') or soup.find('p').find_all('img')
            break
        except Exception as e:
            logger.debug(e)
            logger.warning('Unable to get page from url(%s). Retrying...' % (chapter.url))

    # download and save image from image url
    cnt = 1
    for img in img_list:
        if 'href' in img.attrs:
            img_url = img.attrs['href']
        elif 'data-lazy-src' in img.attrs:
            img_url = img.attrs['data-lazy-src']
        else:
            img_url = img.attrs['src']
        if 'http://imgur.com' in img_url:
            img_url = img_url.replace('imgur.com', 'i.imgur.com')
        try_cnt = 3
        while try_cnt > 0:
            try:
                i = Image.open(BytesIO(requests.get(img_url).content))
                break
            except Exception as e:
                logger.debug(e)
                logger.warning('Unable to download image from url(%s) [%d]' % (img_url, try_cnt))
                time.sleep(5)
                try_cnt -= 1
        if try_cnt > 0:
            ext = os.path.splitext(img_url)[1]
            if 'jpg' in ext:
                ext = '.jpg'
            elif 'jpeg' in ext:
                ext = '.jpg'
            elif 'gif' in ext:
                ext = '.gif'
            elif 'png' in ext:
                ext = '.png'
            filename = '%d%s' % (cnt, ext)
            logger.debug('Downloading [%s] >> [%s]' % (
                    img_url, os.path.join(working_dir, filename)))
            i.save(filename)
            zf.write(filename)
        else:
            logger.warning('Download Failed [%s]' % (img_url))
        cnt += 1
    zf.close()
    logger.warning('Finish archiving [%s] <<' % (zipfile_path))

    # clean working directory
    os.chdir(output)
    shutil.rmtree(working_dir)


def download(url, output='./output'):
    """Download comic file from marumaru entry url

    :param url: URL of title's entry page
    :param output: Output directory

    Usage::

        >>> from marumaru_downloader import download
        >>> download('http://marumaru.in/b/manga/67808',
        >>>          './output')
    """
    s = requests.Session()
    s.headers.update({'User-Agent': CUSTOM_USER_AGENT})

    entry_page_tree = BeautifulSoup(s.get(url).text)
    title = __get_title(entry_page_tree)
    output_dir_path = __make_output_dir(output, title)
    logger.warning('Start downloading [%s(%s)] >> [%s]' % (title, url,
        output_dir_path))
    for chapter in __get_chapters(entry_page_tree, title):
        __save_chapter(s, title, chapter, output_dir_path)
    logger.warning('Finish downloading [%s(%s)] >> [%s]' % (title, url,
        output_dir_path))


if __name__ == '__main__':
    import sys
    url = 'http://marumaru.in/b/manga/67808'
    output = './output'
    logger.setLevel(logging.WARNING)
    if len(sys.argv) == 2:
        url = sys.argv[1]
    elif len(sys.argv) == 3:
        url = sys.argv[1]
        output = sys.argv[2]
    download(url, output)

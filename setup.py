from distutils.core import setup

setup(name='marumaru-downloader',
      version='0.1.3',
      description='Comic Downloader for marumaru.in',
      url='https://github.com/whoknowwhat/marumaru-downloader',
      author='eM',
      author_email='whoknowwhat0623@gmail.com',
      packages=['marumaru_downloader'],
      install_requires=['requests>=2.3.0',
                        'beautifulsoup4>=4.3.2',
                        'Pillow>=2.7.0'],
      zip_safe=False)

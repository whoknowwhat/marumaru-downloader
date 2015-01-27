from distutils.core import setup

setup(name='marumaru-downloader',
      version='0.1.0',
      description='Comic Downloader for marumaru.in',
      url='https://bitbucket.org/whoknowwhat/marumaru-downloader',
      author='eM',
      author_email='whoknowwhat0623@gmail.com',
      packages=['marumaru_downloader'],
      install_requires=['requests==2.3.0',
                        'beautifulsoup4==4.3.2',
                        'PyV8==1.0-dev',
                        'cloudflare-scrape==0.2',
                        'Pillow==2.7.0'],
      zip_safe=False)

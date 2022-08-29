#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# ./spider.py
# Eduardo Banderas Alba
# 2022-07
#
"""
    {0} [-rlpSh] URL

    -r          Descarga imágenes de forma recursiva
    -r -l [N]   Indica el nivel de profundidad para la descarga de las imágenes.
    -p [PATH]   Ruta donde se almacenaran las imágenes.
    -S          Indica qué tipo de fichero buscará. Por defecto, busca las siguientes
                extensiones:
                * .jpg/jpeg
                * .png
                * .gif
                * .bmp
    -h          Muestra esta ayuda.

"""

import os, sys, json
import http.client
import ssl
import hashlib

from time       import time, strftime, localtime
from lxml       import html

try:
  from urllib.parse   import urlparse     #python3
except:
  from urllib         import urlparse

try:
  from urllib.parse   import quote, unquote    #python3
except:
  from urllib         import quote, unquote


class cfg:
  recursive = False
  maxdepth  = 5
  path      = os.path.dirname(os.path.realpath(__file__)) + '/data'
  filetypes  = [
    'jpg',
    'jpeg',
    'bmp',
    'gif'
  ]

  baseurl = None
#cfg

def main():
  parse_arguments()

  sp = spider(cfg.baseurl, cfg.recursive, cfg.maxdepth, cfg.path, cfg.filetypes)

  i = 0
  while cfg.recursive and cfg.maxdepth > i:
    sp.urlprocess(i)
    i += 1
  #endwhile
#main

class spider(object):
  client  = None
  parse   = None
  content = None
  baseurl = None
  files   = []
  follow_url  = []

  download_dir = None
  filetypes = []
  url_processed = []
  headers = {
    'User-Agent': 'Spider v0.1'
  }
  contentType = None

  def __init__(self, url, recursive, maxdepth, download_dir, filetypes):
    self.follow_url.append([])  #Set always level 1
    i = 1
    while recursive and maxdepth > i:  #initialize list
      self.follow_url.append([])
      i += 1

    self.parse = urlparse(url)
    self.baseurl = self.parse.scheme + '://' + self.parse.netloc
    self.download_dir = download_dir
    self.filetypes = filetypes

    print("- Process url {0} in depth {1}".format(url, 0))
    self.get_client_instance()
    self.get_content()
    self.set_follow_url()
    self.get_files()

  def get_client_instance(self):
    self.client = None
    try:
      if self.parse.scheme == 'http':
        self.client = http.client.HTTPConnection(self.parse.netloc)
      else:
        self.client = http.client.HTTPSConnection(
          self.parse.netloc,
          context = ssl._create_unverified_context()
        )
    except:
      print("  - Failed generic http exception")

  #get_client_instance

  def get_content(self):
    if self.client:
      self.url_processed.append(self.parse2url(self.parse))
      path = self.parse.path

      if self.parse.query != '':
        path += '?' + self.parse.query

      try:
        self.client.request('GET', path, headers=self.headers)
        response = self.client.getresponse()
        location = response.getheader('Location')
        self.contentType = response.getheader('content-type')
        self.content     = response.read()
        print("  - Get content: status {0} - content-type {2} {1}"
              .format(response.status, self.parse2url(self.parse), self.contentType))

        response.close()
        self.client.close()

        if location:
          location = self.parse2url(urlparse(location))

          print("  - Redirect {0}".format(location))
          self.parse = urlparse(location)

          self.get_client_instance()
          self.get_content()
        #endif
      except:
        self.client = None
        print("  - Failed generic http exception")
    #endif
  #get_content

  def parse_content(self, query = '//a/@href'):
    out = []
    if self.content is not None and self.content != '':
      body = html.fromstring(self.content)
      out  = body.xpath(query)

    return out
  #parse_content

  def parse2url(self, p):
    url = ''
    if p.scheme in ('http', 'https', ''):
      if p.scheme == '' and p.netloc and p.path == '' and p.query == '':
        pass
      else:
        url = (p.scheme if p.scheme else 'https') + '://' + p.netloc
        if p.netloc == '':  #URL dont have domain
          url = self.parse.scheme + '://' + self.parse.netloc

        if p.path != '':
          if not p.path.startswith('/'):
            url += '/'

          path = unquote(p.path)
          url += quote(path)
        #endif

        if p.query != '':
          url += '?' + p.query
      #endifelse

    return url
  #parse2url

  def set_follow_url(self, depth = 0):
    if depth < len(self.follow_url):
      query_xpath = '//a[contains(@href, "") and ' + \
                         'not(contains(@href, ".zip")) and ' + \
                         'not(contains(@href, ".pdf")) and ' + \
                         'not(contains(@href, ".tar")) and ' + \
                         'not(contains(@href, ".gz"))]/@href'

      for u in self.parse_content(query_xpath):
        url = self.parse2url(urlparse(u))
        if url == '':
          continue

        self.follow_url[depth].append(url)
      #endfor
    #endif
  #set_follow_url

  def get_files(self):
    urls = []
    for type in self.filetypes:
      urls += self.parse_content('//link[contains(@href, ".{0}")]/@href'.format(type)) + \
              self.parse_content('//img[contains(@src, ".{0}")]/@src'.format(type))

    for u in urls:
      url = self.parse2url(urlparse(u))
      if url and url not in self.url_processed:
        self.parse = urlparse(url)
        self.download_file()
      #endif
    #endfor
  #get_files

  def download_file(self):
    if self.client:
      self.get_client_instance()
      self.get_content()

      p = urlparse(self.baseurl)
      filename = self.download_dir + '/' + p.netloc + '/' + \
                 self.contentType  + '/' + hashlib.sha256(self.content).hexdigest()

      dir = os.path.dirname(filename)

      if not os.path.isdir(dir):
        os.makedirs(dir)

      self.write_file(filename)
    #endif
  #download_file

  def write_file(self, filename):
    with open(filename, 'wb') as fw:
      fw.write(self.content)
  #write_file

  def urlprocess(self, depth = 0):
    if depth < len(self.follow_url):
      for u in self.follow_url[depth]:
        if u not in self.url_processed:
          self.parse = urlparse(u)

          print("- Process url {0} in depth {1}".format(u, depth))
          self.get_client_instance()
          self.get_content()
          self.set_follow_url(depth + 1)
          self.get_files()
        #endif
      #endfor
    #endif
  #urlprocess
#class spider


def parse_arguments():
  options_ = [ '-r', '-l', '-p', '-S', '-h' ]
  options  = ' '.join(sys.argv[1:]).strip().split(' ')

  i = 0
  while len(options) > i:
    data = options[i]
    if data == '-r':
      cfg.recursive = True
    elif data == '-h':
      _halt_with_doc('', 0)
    elif data == '-l' or data == '-p' or data == '-S':
      i += 1
      if data == '-l':
        try:      cfg.maxdepth = int(options[i])
        except:   _halt_with_doc('El argumento `-l` debe ser un número, ' + options[i], 1)
      elif data == '-p':
        cfg.path = options[i]
      elif data == '-S':
        cfg.filetype = options[i].split(',')

    i += 1
  #endwhile

  cfg.baseurl = options[-1]

  if cfg.baseurl == '':
    _halt_with_doc('', 0)

  if os.path.isfile(cfg.path):
    _halt_with_doc('La ruta `{0}` es un fichero'.format(cfg.path))

  if cfg.path.endswith('/'):
    cfg.path = cfg.path[0:-1]

  if not os.path.isdir(cfg.path):
    os.makedirs(cfg.path)
#parse_arguments

def _halt_with_doc(msg, code = 0):
  _halt('\n' + msg + '\n' + '-' * 80 + __doc__.format(sys.argv[0]), code)
#_halt_with_doc


def _halt(msg, code = 0):
  try:
    msg = json.dumps(json.loads(msg), indent=2)
  except:
    pass

  sys.stdout.write(msg.strip() + '\n')
  sys.exit(code)
#_halt


if __name__ == "__main__":
  try:    reload(sys); sys.setdefaultencoding("utf8")
  except: pass

  main()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# dns_blacklist_update.py
# Eduardo Banderas Alba
#
# Lista negra de las zonas DNS.
# Genera una lista negra de nombres de dominio basada en:
#   * someonewhocares.org
#   * malwaredomainlist.com
#   * pgl.yoyo.org
#   * mirror1.malwaredomains.com
#
#
# Configuración, debe existir un fichero llamado named.conf.blacklist y el directorio con la zona
# configurada ./blacklist/blacklist.zone
#
import httplib
import sys


class cfg:
  blacklist_filename = '/etc/bind/named.conf.blacklist'
  _blacklist = [
    {
      'host': 'www.malwaredomainlist.com',
      'uri': '/hostslist/hosts.txt',
      'format': 'hostformat'
    },
    {
      'host': 'mirror1.malwaredomains.com',
      'uri': '/files/justdomains',
      'format': 'domain_per_line'
    },
    {
      'host': 'pgl.yoyo.org',
      'uri': '/adservers/serverlist.php?hostformat=hosts&showintro=0&mimetype=plaintext&useip=0.0.0.0',
      'format': 'hostformat'
    },
    {
      'host': 'someonewhocares.org',
      'uri': '/hosts/hosts',
      'format': 'hostformat'
    }
  ]
#cfg


def main():
  for mdl in cfg._blacklist:
    result = get_blacklist(mdl['host'], mdl['uri'])
    generate_bind_blacklist(result, mdl['format'])
  return
#main

def generate_bind_blacklist(data, format):
  try:
    with open(cfg.blacklist_filename, 'r') as fr:
      load_blacklisted_domains = fr.read()
  except:
    load_blacklisted_domains = ''

  for d in data.split('\n'):
    value = d[0: d.find('#')].strip()  # Limpieza de comentarios en línea.

    if value == '':    continue

    if   format == 'hostformat':
      try:
        ip, domain = value.split()
      except:
        pass

    elif format == 'domain_per_line':
      domain = value

    else:
      print('No se reconoce formato')
      continue

    if load_blacklisted_domains.find(domain) > -1:    continue  # Existe el dominio

    zone = 'zone "' + domain + '" {type master; file "/etc/bind/blacklist/blacklist.zone";};\n'
    with open(cfg.blacklist_filename, 'a') as fw:
      fw.writelines(zone)

    load_blacklisted_domains += zone
#generate_bind_blacklist


def get_blacklist(host, uri = '/', ssl=False):
  result = ''
  if ssl:    http = httplib.HTTPSConnection(host)
  else:      http = httplib.HTTPConnection(host)

  http.connect()
  try:
    http.request('GET', uri)
    response = http.getresponse()
    result   = response.read()

  except (httplib.CannotSendRequest, httplib.BadStatusLine):
    http.close()
    return
  #try:  except

  if response.status != 200:
    result = ''

  return result
#http_connect


def _halt_with_doc(msg, code):
  _halt('\n' + msg + '\n' + '-' * 80 + __doc__.format(sys.argv[0]), code)
#_halt_with_doc


def _halt(msg, code):
  sys.stderr.write(msg)
  sys.exit(0 + code)
#_halt


if __name__ == '__main__':
  try:
    sys.setdefaultencoding("utf8")
  except:
    reload(sys)
    sys.setdefaultencoding("utf8")

  main()

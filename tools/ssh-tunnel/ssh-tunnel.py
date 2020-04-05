#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# management.py
# Eduardo Banderas Alba
#
# Abre tunel inverso contra un servidor
#
import os
import sys
import httplib
import json
from subprocess import Popen, PIPE, call
from signal import SIGTERM
from time import sleep, time, ctime
from base64 import b64encode


class config:
  hostname = None
  http = {
    'host': '',
    'user': '',  # Auth basic
    'pass': ''
  }
  ssh_options = {
    'priv'   : '/root/.ssh/id_ecdsa.key',
    'user'   : 'username',
    'port'   : '22',
    'host'   : 'sshhost.example.net',
    'options': ('-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no '+
                '-o ServerAliveInterval=60 -o ServerAliveCountMax=2 ' +
                '-o ExitOnForwardFailure=yes -o PasswordAuthentication=no ' +
                '-o ConnectTimeout=15 -N'),
    'reverse': 'localhost:8443:localhost:22',
  }
  wait_for_next = 1200
#config


def main():
  tunneling = ssh(cfg.ssh_options)

  if cfg.hostname is None:
    cfg.hostname = get_hostname()

  while True:
    action = request(**cfg.http)

    if action == 'tunneling':    tunneling.start()
    else:                        tunneling.stop()

    sleep(cfg.wait_for_next)
  #while
#main


def logging(msg):
  with open('/var/log/ssh-tunnel.log', 'a') as f:
    f.writelines(str(msg) + '\n')
#logging


def get_hostname():
  filename = '/etc/hostname'
  with open(filename, 'r') as f:
    v = f.read()
  return v.strip()
#get_hostname


def request(host, user, passwd):
  try:                http = httplib.HTTPSConnection(host)
  except Exception:   return ''

  headers = { 'Authorization': 'Basic ' + b64encode(user + ':' + passwd) }
  http.request('GET', '/{}'.format(cfg.hostname), headers=headers)
  result = http.getresponse().read()
  http.close()
  try:     return json.loads(result)
  except:  return result.strip()
#request


def get_process_by_name(name):
  # Capture process id
  arr = name.split()
  if len(arr) > 1:      start, end = (arr[0], arr[-1])
  else:                 start, end = (arr[0], '')

  p = Popen('/bin/ps -A -o "pid,cmd"', shell=True, stdout=PIPE, stderr=PIPE)
  pid = 0
  for real in p.stdout.readlines():
    if pid > 0:  continue  # Existe proceso
    c_pid, cmd = real.strip().split(' ', 1)
    if cmd.startswith(start) and cmd.endswith(end):
      pid = int(c_pid)

  return pid
#get_process_by_name


class ssh(object):

  def __init__(self, settings):
    self.command = ('/usr/bin/ssh {options} -i {priv} -p {port} {user}@{host} -R {reverse}'
                    .format(**settings))

    self.pid = get_process_by_name(self.command)

    if os.path.exists(settings['priv']):
      stat = os.stat(settings['priv'])
      perm = oct(stat.st_mode)
      if perm[-3:] != '600':
        logging(str(ctime()) + ' - Check file permission ' + settings['priv'])

    else:
      logging(str(ctime()) + ' - Not exists priv key ' + settings['priv'])
  #__init__

  def start(self):
    if self.pid == 0:
      Popen(self.command, shell=True, stdout=PIPE, stderr=PIPE)
      sleep(1.5)
      logging(str(ctime()) + ' - Initialize SSH Tunnel')
      self.pid = get_process_by_name(self.command)
  #start

  def stop(self):
    try:
      if self.pid > 0:
        os.kill(self.pid, SIGTERM)
        sleep(0.2)
        logging(str(ctime()) + ' - SSH Tunnel stopped')
        self.pid = 0

    except Exception:
      pass
  #stop
#class ssh


if __name__ == '__main__':
  try:
    sys.setdefaultencoding("utf8")
  except:
    reload(sys)
    sys.setdefaultencoding("utf8")

  main()

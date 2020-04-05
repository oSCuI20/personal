#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# ./convert_consignment_to_contaplus.py
# Eduardo Banderas Alba
#
# Conversor de los ficheros XML que devuelve el banco a ContaPlus
"""
  Uso: {0} --consignment <filename> --seat dd/mm/YYYY,"CONCEPTO",nseat --refund <directory with xmlfile>
  Documentación del script. Cómo usarlo y parámetros

  --consignment  Fichero de remesas
  --seat         Asiento al que corresponde
  --refund       Directorio con los ficheros xml de las devoluciones
"""
import sys
import os
import json

from time import strftime, strptime

try:
  import xmltodict
except:
  print('ERROR - No se encuentra el módulo xmltodict, instala el paquete python-xmltodict')
  sys.exit(1)


def main():
  args = parse_arguments()
  ignore_clients = [ '430060005', '430020093' '430070323', '430060008', '430020201' ]
  print(' * Cargando fichero de remesa: {}'.format(args['consignment']))

  val = {
    'seat': [ args['seat']['date'], args['seat']['concept'], args['seat']['nseat']],
    'consignment': load_consignment(args['consignment'])
  }

  if len(args['refund']) == 0:
    write2contaplus(val)  # Escribir fichero para importar a contaplus

  if len(args['refund']) > 0:
    refunds = []
    for xmlrefund in args['refund']:
      refunds += load_xmlfile(xmlrefund)

    total_refund = len(refunds)
    total_import = 0.00
    hit = []
    for consign in val['consignment']:
      if consign[4] in ignore_clients:
        print(' * Trimestral cliente: {} '.format(json.dumps(consign)))
        continue

      ref = False
      for refund in refunds:
        if consign[2] == refund[2]:  # Si coincide, el cliente ha devuelto el recibo.
          total_import += float(refund[1])
          ref = True
      #for refund

      if not ref:
        hit.append(consign)
    #for consign

    print(' * Devoluciones totales {} - Importe total {}'.format(total_refund, total_import))
    val = {
      'seat': [ args['seat']['date'], args['seat']['concept'], args['seat']['nseat'] ],
      'consignment': hit,
      'refund': True
    }

    #print(json.dumps(val, indent=2))
    write2contaplus(val)  # Escribir fichero para importar a contaplus
#main


def write2contaplus(data):
  """
    data = {
      'filename': '',
      'seat': [ date, concept, nseat ],
      'consignment': [ values ],
      'total': float(),
      'refund': True | False
    }
  """
  print(' * Importando remesa a contaplus')

  if 'seat' not in data or len(data['seat']) != 3:
    print('Se ha producido un error inesperado, write2contaplus no key seat')
    sys.exit(1)

  try:
    config = {
      'filename': 'c1914_sepa_{}_mensual.contaplus'.format(data['seat'][1].split()[-1].lower()),
      'total' : float(data['total']) if 'total'  in data else 0.00,
      'refund': data['refund']       if 'refund' in data else False,
      'date'    : data['seat'][0],
      'concept' : data['seat'][1],
      'nseat'   : data['seat'][2]
    }
  except KeyError as err:
    print('Se ha producido un error inesperado, write2contaplus config')
    print('ERROR\n{}'.format(err))
    sys.exit(1)

  except ValueError:
    print('Se ha producido un error inesperado, write2contaplus config')
    sys.exit(1)

  if config['refund']:  config['filename'] += '.cobros.txt'
  else:                 config['filename'] += '.txt'

  if os.path.isfile(config['filename']):
    print(' * Ya se ha generado un fichero, si quieres volver a generarlo, eliminalo')
    print(' * El fichero no se va a generar')
    return ;

  col1  = 23; col2  = 31; col3  = 23; col4  = 18; col5  = 8;  col6  = 16;
  col7  = 5;  col8  =  5; col9  = 10; col10 = 17; col11 = 6;  col12 = 16;
  col13 = 16; col14 = 16; col15 = 28; col16 = 16; col17 = 16; col18 = 17;
  col19 = 19;

  #refund columns
  col20 = 16; col21 = 17; col22 =  10; col23 =  7; col24 = 13; col25 = 36; col26 =  5;
  col27 =  6; col28 = 16; col29 = 209; col30 = 81; col31 = 65; col32 = 12; col33 = 16;
  col34 = 13; col35 = 83; col36 =   4; col37 = 51; col38 = 76; col39 = 44; col40 = 26;

  if config['refund']:
    col9 = 8; col10 = 19;

  end = "\r\n"
  #ARRAY position => transactionId, quota, iban, bussiness, cid
  with open(config['filename'], 'w') as wf:
    for consign in data['consignment']:
      config['total'] += float(consign[1])

      val1 = add_left_spaces('12345{}{}'.format(config['date'], consign[4]), col1)

      val2  = add_left_spaces('0.00', col2) ; val4  = add_left_spaces('0.00', col4)
      val5  = add_left_spaces('0',    col5) ; val6  = add_left_spaces('0.00', col6)
      val7  = add_left_spaces('0.00', col7) ; val8  = add_left_spaces('0.00', col8)
      val10 = add_left_spaces('00',   col10); val11 = add_left_spaces('0',    col11)
      val9  = add_left_spaces(config['nseat'],   col9)
      val3  = add_left_spaces(config['concept'], col3)

      val12 = add_left_spaces('0.000000', col12); val13 = add_left_spaces('0.00',  col13)
      val14 = add_left_spaces('0.00',     col14); val15 = add_left_spaces('0.002', col15)

      if config['refund']:
        val17 = add_left_spaces(str(consign[1]), col17)
        val16 = add_left_spaces('0.00',  col16)

      else:
        val16 = add_left_spaces(str(consign[1]), col16)
        val17 = add_left_spaces('0.00',  col17)

      val18 = add_left_spaces('0.00F', col18)
      val19 = add_left_spaces('0',   col19)

      wf.write(val1  +  val2 +  val3 +  val4 +  val5 +  val6 +  val7 +  val8 +  val9 + val10 +
               val11 + val12 + val13 + val14 + val15 + val16 + val17 + val18 + val19)

      if config['refund']:
        val20 = add_left_spaces('0.00', col20); val21 = add_left_spaces('0.00F', col21)
        val22 = add_left_spaces('EF',   col22); val23 = add_left_spaces('0F',    col23)
        val24 = add_left_spaces('F',    col24); val25 = add_left_spaces('0.00',  col25)
        val26 = add_left_spaces('0.00', col26); val27 = add_left_spaces('0',     col27)
        val28 = add_left_spaces('0.00', col28); val29 = add_left_spaces('0',     col29)
        val30 = add_left_spaces('0',    col30); val31 = add_left_spaces('F',     col31)
        val32 = add_left_spaces('FF',   col32); val33 = add_left_spaces('0.00',  col33)
        val34 = add_left_spaces('0',    col34); val35 = add_left_spaces('F',     col35)
        val36 = add_left_spaces('0',    col36); val37 = add_left_spaces('0.00',  col37)
        val38 = add_left_spaces('0.00', col38); val39 = add_left_spaces('0F0',   col39)
        val40 = add_left_spaces('0',    col40)

        wf.write(val20 + val21 + val22 + val23 + val24 + val25 + val26 + val27 + val28 + val29 +
                 val30 + val31 + val32 + val33 + val34 + val35 + val36 + val37 + val38 + val39 + val40)
      #if config['refund']

      wf.write(end)
    #for consign
    if not config['refund']:
      val1 = add_left_spaces('12345{}705000000'.format(config['date']), col1)
    else:
      val1 = add_left_spaces('12345{}520800000'.format(config['date']), col1)

    val2  = add_left_spaces('0.00', col2);  val4  = add_left_spaces('0.00', col4)
    val5  = add_left_spaces('0',    col5);  val6  = add_left_spaces('0.00', col6)
    val7  = add_left_spaces('0.00', col7);  val8  = add_left_spaces('0.00', col8)
    val10 = add_left_spaces('00',   col10); val11 = add_left_spaces('0',    col11)
    val9  = add_left_spaces(config['nseat'],   col9)
    val3  = add_left_spaces(config['concept'], col3)

    val12 = add_left_spaces('0.000000', col12); val13 = add_left_spaces('0.00',  col13)
    val14 = add_left_spaces('0.00',     col14); val15 = add_left_spaces('0.002', col15)

    if config['refund']:
      val17 = add_left_spaces('0.00', col17)
      val16 = add_left_spaces(str(format(config['total'], '.2f')),  col16)

    else:
      val16 = add_left_spaces('0.00', col16)
      val17 = add_left_spaces(str(format(config['total'], '.2f')),  col17)

    val18 = add_left_spaces('0.00F', col18)
    val19 = add_left_spaces('0',   col19)
    wf.write(val1  +  val2 +  val3 +  val4 +  val5 +  val6 +  val7 +  val8 +  val9 + val10 +
             val11 + val12 + val13 + val14 + val15 + val16 + val17 + val18 + val19)

    if config['refund']:
      val20 = add_left_spaces('0.00', col20); val21 = add_left_spaces('0.00F', col21)
      val22 = add_left_spaces('EF',   col22); val23 = add_left_spaces('0F',    col23)
      val24 = add_left_spaces('F',    col24); val25 = add_left_spaces('0.00',  col25)
      val26 = add_left_spaces('0.00', col26); val27 = add_left_spaces('0',     col27)
      val28 = add_left_spaces('0.00', col28); val29 = add_left_spaces('0',     col29)
      val30 = add_left_spaces('0',    col30); val31 = add_left_spaces('F',     col31)
      val32 = add_left_spaces('FF',   col32); val33 = add_left_spaces('0.00',  col33)
      val34 = add_left_spaces('0',    col34); val35 = add_left_spaces('F',     col35)
      val36 = add_left_spaces('0',    col36); val37 = add_left_spaces('0.00',  col37)
      val38 = add_left_spaces('0.00', col38); val39 = add_left_spaces('0F0',   col39)
      val40 = add_left_spaces('0',    col40)

      wf.write(val20 + val21 + val22 + val23 + val24 + val25 + val26 + val27 + val28 + val29 +
               val30 + val31 + val32 + val33 + val34 + val35 + val36 + val37 + val38 + val39 + val40)

    wf.write(end)
  #close file

  print(' * Remesa, {} clientes, importe total: {:.2f}€'.format(len(data['consignment']), config['total']))
#write2contaplus


def add_left_spaces(string, num):
  return '{}{}'.format(str(' ' * (num - len(string))), string)
#add_left_spaces


def load_xmlfile(ifile):
  refund = []
  with open(ifile, 'r') as f:
    doc = xmltodict.parse(f.read())
  xml = doc['Document']['CstmrPmtStsRpt']['OrgnlPmtInfAndSts']

  if not isinstance(xml, list):
    xml = [ xml ]

  for x in xml:
    info = x['TxInfAndSts']
    if   isinstance(info, dict):
      transactionId = toUTF8(list(find('OrgnlEndToEndId', info))[0] + list(find('MndtId', info))[0])
      bussiness     = toUTF8(list(find('OrgnlTxRef', info))[0]['Dbtr']['Nm'])
      iban          = toUTF8(list(find('OrgnlTxRef', info))[0]['DbtrAcct']['Id']['IBAN'])
      quota         = float(list(find( 'OrgnlTxRef', info))[0]['Amt']['InstdAmt']['#text'])
      refund.append([ transactionId, format(quota, '.2f'), iban.upper(), bussiness ])

    elif isinstance(info, list):
      for i in info:
        transactionId = toUTF8(i['OrgnlEndToEndId'] + i['OrgnlTxRef']['MndtRltdInf']['MndtId'])
        bussiness     = toUTF8(i['OrgnlTxRef']['Dbtr']['Nm'])
        iban          = toUTF8(i['OrgnlTxRef']['DbtrAcct']['Id']['IBAN'])
        quota         = float(i['OrgnlTxRef']['Amt']['InstdAmt']['#text'])
        refund.append([ transactionId, format(quota, '.2f'), iban.upper(), bussiness ])

  print(' * Número devoluciones en fichero {}, {}'.format(ifile, len(refund)))
  return refund
#load_xmlfile


def load_consignment(ifile):
  clients = []

  total = 0.00
  transaction_pos = 80
  quota_pos       = (88,  99)
  cid_pos         = (358, 367)
  iban_pos        = (403, 427)
  bussines_pos    = (118, 328)
  with open(ifile, 'r') as f:
    for line in f:
      if line.find('0319143003') < 0:    continue

      pos   = line.find('OOFFCASH')
      count = len('OOFFCASH')

      transactionId = toUTF8(line[len('0319143003'):transaction_pos]).strip()
      quota         = int(line[quota_pos[0]:quota_pos[1]]) * 0.01

      cid   = toUTF8(line[cid_pos[0]:cid_pos[1]]).strip()
      iban  = toUTF8(line[iban_pos[0]:iban_pos[1]]).strip()

      bussiness = toUTF8(line[bussines_pos[0]:bussines_pos[1]]).strip()

      if len(cid) != 9:
        print('El cliente con identificador: {} no tiene un formato válido'.format(cid))
        print('Datos del cliente: ')
        print('  * Id Transacción: {}'.format(transactionId))
        print('  * Id ContaPlus: {}'.format(cid))
        print('  * Cuenta bancaria: {}'.format(iban))
        print('  * Empresa: {}'.format(bussiness))
        sys.exit(1)

      total += float(format(quota, '.2f'))
      clients.append([ transactionId, format(quota, '.2f'), iban.upper(), bussiness, cid ])

    print('Remesa total: {}'.format(total))
  return clients
#load_consignment


def toUTF8(string, encoding = 'ISO-8859-1'):
  return string.decode(encoding).encode('UTF8')
#toUTF8


def parse_arguments():
  args = ' '.join(sys.argv[1:])

  if len(args) < 1:
    print('Error, no se han pasado argumentos')
    print(__doc__.format(sys.argv[0]))
    sys.exit(1)

  #--param1 value1 --param2 other value
  options_ = [ 'consignment', 'refund', 'seat', 'help' ]   # Valid options
  options  = args.split('--')[1:]

  arguments = { 'consignment': '', 'refund': '', 'seat': '' }

  if len(options) == 0:
    print('Error, no se han pasado argumentos o el argumento no se reconoce')
    sys.exit(1)

  for option in options:
    try:
      key, value = option.split(' ', 1)
      key, value = (key.strip(), value.strip())
    except:
      key, value = (option.strip(), None)

    if key not in options_:
      print('No se reconoce la opción {0}'.format(key))
      sys.exit(1)

    if key == 'help':
      print(__doc__.format(sys.argv[0]))
      sys.exit(0)

    arguments[key] = value
  #for option

  if not os.path.isfile(arguments['consignment']):
    print('--consignment    No existe el fichero de remesa.')
    sys.exit(1)

  refund = []
  if arguments['refund'] != '' and not os.path.isdir(arguments['refund']):
    print('--refund    No existe el directorio o no es un directorio')
    sys.exit(1)

  if arguments['refund'] != '' and os.path.isdir(arguments['refund']):
    for xmlfile in os.listdir(arguments['refund']):
      if xmlfile.lower().endswith('.xml'):
        refund.append(arguments['refund'] + '/' + xmlfile)

    if len(refund) == 0:
      print('--refund   Error, no se encuentra ningún fichero XML en el directorio {}'.format(arguments['refund']))
      sys.exit(1)

  arguments['refund'] = refund

  if arguments['seat'] == '':
    print('--seat    No se han indicado los parámetros del asiento')
    sys.exit(1)

  try:
    in_date, in_concept, in_seat = arguments['seat'].split(',')
  except:
    print('--seat    No se ha indicado los parámetros correctamente, <fecha>,<concepto>,<numero asiento>')
    sys.exit(1)

  try:
    strftime('%Y%m%d', strptime(in_date, '%d/%m/%Y'))
  except:
    print('El formato de la fecha no es válido, debe ser d/m/Y - 01/12/2015')
    sys.exit(1)

  arguments['seat'] = {
    'date': strftime('%Y%m%d', strptime(in_date, '%d/%m/%Y')),
    'concept': in_concept.upper(),
    'nseat': in_seat
  }

  return arguments
#parse_arguments


def find(key, dictionary):
  for k, v in dictionary.iteritems():
    if k == key:
      yield v
    elif isinstance(v, dict):
      for result in find(key, v):
        yield result
    elif isinstance(v, list):
      for d in v:
        for result in find(key, d):
          yield result
#find

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

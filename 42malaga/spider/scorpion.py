#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# ./scorpion.py
# Eduardo Banderas Alba
# 2022-07
#
"""
    {0} file1 [file2]
"""

import os, sys, json

from PIL import Image, TiffImagePlugin, ExifTags

FILES = []

def main():
  parse_arguments()

  for img in FILES:
    exif = {}
    try:
      im   = Image.open(img)
      data = im._getexif()
    except:
      continue

    if data is not None:
      for k, v in data.items():
        if k in ExifTags.TAGS:
          if   isinstance(v, TiffImagePlugin.IFDRational):
            v = float(v)
          elif isinstance(v, tuple):
            v = tuple(float(t) if isinstance(t, TiffImagePlugin.IFDRational) else t for t in v)
          elif isinstance(v, bytes):
            v = v.decode(errors="replace")

          exif[ExifTags.TAGS[k]] = v
      #endfor
    im.close()

    print(img)
    print(exif)
  #endfor
#main

def parse_arguments():
  if len(sys.argv) < 1:
    print("No se han introducido ningún fichero")

  for f in ' '.join(sys.argv[1:]).strip().split(' '):
    if not os.path.isfile(f) or not os.path.exists(f):
      print("El fichero {0} no existe o no es un fichero".format(f))
      sys.exit(1)
    FILES.append(f)
#parse_arguments

if __name__ == "__main__":
  try:    reload(sys); sys.setdefaultencoding("utf8")
  except: pass

  main()

El rol de *httpd* instala los siguientes paquetes por defecto

* httpd
* mod_ssl
* openssl

El servicio httpd incluye las siguientes rutas:

* conf.modules.d/*.conf    # Carga los módulos
* conf.d/servername.conf   # Añade la directiva ServerName por defecto.
* conf.d/*.mod.conf        # Configuración de los módulos
* conf.d/*.vhost.conf      # VirtualHost

httpd:
  default_servername: host01.my.home
  timeout: 60
  keepalive: 'Off'
  maxkeepaliverequest: 120
  keepalivetimeout: 45

  prefork: {
    'startservers': 4,
    'minspare': 16,
    'maxspare': 64,
    'limit': 128,
    'maxclients': 128,
    'max_req_per_child': 512
  }
  worker: {
    'startservers': 4,
    'minspare': 16,
    'maxspare': 64,
    'maxclients': 256,
    'th_per_child': 8,
    'max_req_per_child': 128
  }
  header: {
    'set': [
      'X-XSS-Protection "1; mode=block"',
      'X-Content-Type-Options: nosniff',
      'Strict-Transport-Security "max-age=31536000; includeSubDomains"'
    ],
    'append': [
      'X-Frame-Options SAMEORIGIN'
    ]
  }
  ssl_default_cert: {
    'crt': '',
    'key': '',
    'chain': ''
  }
  ssl: True
  letsencrypt: False
  selfsigned: False
  vhost:
    - {
        'ssl': {
          'crt': '/etc/letsencrypt/live/owncloud.my.home/cert.pem',
          'key': '/etc/letsencrypt/live/owncloud.my.home/privkey.pem',
          'chain': '/etc/letsencrypt/live/owncloud.my.home/chain.pem'
        },
        'document_root': '/var/www/owncloud',
        'server_name': 'http.vhost.my.home',
        'server_alias': [ ],
        'redirect_https': True,
        'logdirectory': '',
        'allow_request_method': [ 'GET', 'POST', 'OPTIONS', 'HEAD', 'PUT', 'DELETE' ],
        'custom_for_site': ''
      }

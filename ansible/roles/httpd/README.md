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
  default_servername: owncloud.my.home
  timeout: 60
  keepalive: 'Off'
  maxkeepaliverequest: 120
  keepalivetimeout: 45

  modules:
    - other_mod
    - more_packages

  prefork:
    {
      'startservers': 4,
      'minspare': 16,
      'maxspare': 64,
      'limit': 128,
      'maxclients': 128,
      'max_req_per_child': 512
    }
  worker:
    {
      'startservers': 4,
      'minspare': 16,
      'maxspare': 64,
      'maxclients': 256,
      'th_per_child': 8,
      'max_req_per_child': 128
    }
  header:
    {
      'set':
        - 'X-XSS-Protection "1; mode=block"'
        - 'X-Content-Type-Options: nosniff'
        - 'Strict-Transport-Security "max-age=31536000; includeSubDomains"'
      'append':
        - 'X-Frame-Options SAMEORIGIN'
    }
  virtualhost:
    - {
        'documentroot': ''
      }
  ssl_default_cert:
    {
      'crt': ''
      'key': ''
      'chain': ''
    }
  ssl_certs:
    - {
        'crt': ''
        'key': ''
        'chain': ''
      }

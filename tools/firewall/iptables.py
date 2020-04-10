#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Eduardo Banderas Alba
#
# Implement a firewall on linux system with iptables
#
"""
    {
      "config": {
        "mode": "server",   #server | router
        "type": "CentOS",   # CentOS | Debian
        "policy": {
          "input": "DROP",
          "forward": "DROP"
        },
        "inet": {
          "external": { "name": "ens18", "ipaddr": "xxx.xxx.xxx.xxx" },
          "internal": [
            { "name": "lan0", "range": "172.16.0.0/24" },
            { "name": "ap0", "range": "172.16.1.0/24" },
          ]
        }
      },
      "incoming": [
        { "src": "*",              "dst": "*",  "port": "22910", "proto": "tcp" },
        { "src": "*",              "dst": "*",  "port": "25",    "proto": "tcp" },
        { "src": "*",              "dst": "*",  "port": "80",    "proto": "tcp" },
        { "src": "*",              "dst": "*",  "port": "443",   "proto": "tcp" },
        { "src": "*",              "dst": "*",  "port": "110",   "proto": "tcp" },
        { "src": "*",              "dst": "*",  "port": "143",   "proto": "tcp" },
        { "src": "*",              "dst": "*",  "port": "465",   "proto": "tcp" },
        { "src": "*",              "dst": "*",  "port": "587",   "proto": "tcp" },
        { "src": "*",              "dst": "*",  "port": "993",   "proto": "tcp" },
        { "src": "*",              "dst": "*",  "port": "995",   "proto": "tcp" },
        { "src": "*",              "dst": "*",  "port": "5280",  "proto": "tcp" },
        { "src": "*",              "dst": "*",  "port": "5281",  "proto": "tcp" },
        { "src": "xxx.xxx.xxx.xxx", "dst": "*",  "port": "3306",  "proto": "tcp" },
        { "src": "xxx.xxx.xxx.xxx", "dst": "*",  "port": "3306",  "proto": "tcp" },
        { "src": "xxx.xxx.xxx.xxx", "dst": "*",  "port": "3306",  "proto": "tcp" },
        { "src": "xxx.xxx.xxx.xxx", "dst": "*",  "port": "3306",  "proto": "tcp" },
        { "src": "xxx.xxx.xxx.xxx", "dst": "*",  "port": "161",   "proto": "udp" }
      ],
      "outgoing": [
        { "src": "*",              "dst": "*",  "port": "22910", "proto": "tcp" },
        { "src": "*",              "dst": "*",  "port": "22",    "proto": "tcp" },
        { "src": "*",              "dst": "*",  "port": "53",    "proto": "tcp" },
        { "src": "*",              "dst": "*",  "port": "53",    "proto": "udp" },
        { "src": "*",              "dst": "*",  "port": "123",   "proto": "udp" }
      ],
      "forwarding": [
        { "src": "*",              "dst": "*",  "port": "22910", "proto": "tcp" }
      ]
    }
"""
import sys
import os
import json


def main():
  if len(sys.argv) == 1:
    print('Argumento debe ser fichero json con la configuración del Firewall')
    sys.exit(1)

  if not os.path.isfile(sys.argv[1]):
    print('No existe el fichero')
    sys.exit(1)

  with open(sys.argv[1], 'r') as f:
    try:
      loaded = json.loads(f.read())
    except:
      loaded = eval(f.read())

  check_system_support(loaded['config']['type'])

  set_default_policy(loaded['config'])
  chain_rules(loaded['config'])

  set_general_filter(loaded['config'])
  spoofing_rules(
    loaded['config']['inet']['external']['name'],
    loaded['config']['type']
  )
  icmp_rules(
    loaded['config']['inet']['external']['name'],
    loaded['config']['type']
  )
  smb_rules(
    loaded['config']['inet']['external']['name'],
    loaded['config']['type']
  )

  allow_incoming_traffic(loaded)
  allow_outgoing_traffic(loaded)


  if loaded['config']['mode'] == 'router':
    if len(loaded['config']['inet']['internal']) > 0:
      allow_forwarding_traffic(loaded)
      postrouting(loaded)
      print('\necho 1 > /proc/sys/net/ipv4/ip_forward')

    else:
      print('No se ha configurado ningún interfaz interno')

  drop_rules(loaded['config']['type'])
  sys.exit(1)
#main


def print_debian_rules(out):
  for rule in out.split('\n'):
    if rule.startswith('#'):
      print('\n' + rule)
    else:
      if rule:
        print('/sbin/iptables ' + rule)
#print_debian_rules


def print_centos_rules(out):
  for rule in out.split('\n'):
    if rule.startswith('#'):
      print('\n' + rule)
    else:
      if rule:
        print(rule)
#print_centos_rules


def check_system_support(system):
  support = ['CentOS', 'Debian']
  if system not in support:
    print('System type not recognized')
    sys.exit(1)
#check_system_support


def allow_forwarding_traffic(conf):
  out = '# Allow forwarding traffic\n'
  if len(conf['config']['inet']['internal']) > 1:
    out += '## Allow internal traffic\n'
    for first_inet in conf['config']['inet']['internal']:
      temp = '-A FORWARD -s ' + first_inet['range'] + ' '
      for second_inet in conf['config']['inet']['internal']:
        if first_inet != second_inet:
          out += temp + '-d ' + second_inet['range'] + ' -j ACCEPT\n'
      #for second_inet
    #for first_inet
  #if len(conf['config']['inet']['internal'])

  out += '## Allow internal traffic to internet\n'
  for cnf in conf['forwarding']:
    out += ('-A FORWARD -p ' + cnf['proto'] + ' --dport ' + cnf['port'] + ' ' +
            '-m conntrack --ctstate NEW,ESTABLISHED ')
    if cnf['iface'] != '*':      out += '-i ' + cnf['iface'] + ' '
    if cnf['src'] != '*':        out += '-s ' + cnf['src'] + ' '
    if cnf['dst'] != '*':        out += '-d ' + cnf['dst'] + ' '
    if cnf['proto'] == 'tcp':    out += '-j TCPACCEPT\n'
    if cnf['proto'] == 'udp':    out += '-j ACCEPT\n'

    out += ('-A FORWARD -p ' + cnf['proto'] + ' --sport ' + cnf['port'] + ' ' +
            '-m conntrack --ctstate ESTABLISHED ')
    if cnf['iface'] != '*':      out += '-o ' + cnf['iface'] + ' '
    if cnf['src'] != '*':        out += '-d ' + cnf['src'] + ' '
    if cnf['dst'] != '*':        out += '-s ' + cnf['dst'] + ' '
    if cnf['proto'] == 'tcp':    out += '-j TCPACCEPT\n'
    if cnf['proto'] == 'udp':    out += '-j ACCEPT\n'

  if conf['config']['type'] == 'CentOS':
    print_centos_rules(out)

  if conf['config']['type'] == 'Debian':
    print_debian_rules(out)
#allow_forwarding_traffic


def allow_outgoing_traffic(conf):
  out = '# Allow outgoing traffic\n'
  for cnf in conf['outgoing']:
    out += ('-A INPUT -p ' + cnf['proto'] + ' --sport ' + cnf['port'] + ' ' +
            '-m conntrack --ctstate ESTABLISHED ')
    if cnf['iface'] != '*':      out += '-i ' + cnf['iface'] + ' '
    if cnf['src'] != '*':        out += '-d ' + cnf['src'] + ' '
    if cnf['dst'] != '*':        out += '-s ' + cnf['dst'] + ' '
    if cnf['proto'] == 'tcp':    out += '-j TCPACCEPT\n'
    if cnf['proto'] == 'udp':    out += '-j ACCEPT\n'

    out += ('-A OUTPUT -p ' + cnf['proto'] + ' --dport ' + cnf['port'] + ' ' +
            '-m conntrack --ctstate NEW,ESTABLISHED ')
    if cnf['iface'] != '*':      out += '-o ' + cnf['iface'] + ' '
    if cnf['src'] != '*':        out += '-s ' + cnf['src'] + ' '
    if cnf['dst'] != '*':        out += '-d ' + cnf['dst'] + ' '
    if cnf['proto'] == 'tcp':    out += '-j TCPACCEPT\n'
    if cnf['proto'] == 'udp':    out += '-j ACCEPT\n'

  if conf['config']['type'] == 'CentOS':
    print_centos_rules(out)

  if conf['config']['type'] == 'Debian':
    print_debian_rules(out)
#allow_outgoing_traffic


def allow_incoming_traffic(conf):
  out = '# Allow incoming traffic\n'
  for cnf in conf['incoming']:
    out += ('-A INPUT -p ' + cnf['proto'] + ' --dport ' + cnf['port'] + ' ' +
            '-m conntrack --ctstate NEW,ESTABLISHED ')

    if cnf['iface'] != '*':      out += '-i ' + cnf['iface'] + ' '
    if cnf['src'] != '*':        out += '-s ' + cnf['src'] + ' '
    if cnf['dst'] != '*':        out += '-d ' + cnf['dst'] + ' '
    if cnf['proto'] == 'tcp':    out += '-j TCPACCEPT\n'
    if cnf['proto'] == 'udp':    out += '-j ACCEPT\n'

    out += ('-A OUTPUT -p ' + cnf['proto'] + ' --sport ' + cnf['port'] + ' ' +
            '-m conntrack --ctstate ESTABLISHED ')
    if cnf['iface'] != '*':      out += '-o ' + cnf['iface'] + ' '
    if cnf['src'] != '*':        out += '-d ' + cnf['src'] + ' '
    if cnf['dst'] != '*':        out += '-s ' + cnf['dst'] + ' '
    if cnf['proto'] == 'tcp':    out += '-j TCPACCEPT\n'
    if cnf['proto'] == 'udp':    out += '-j ACCEPT\n'

  if conf['config']['type'] == 'CentOS':
    print_centos_rules(out)

  if conf['config']['type'] == 'Debian':
    print_debian_rules(out)
#allow_incoming_traffic


def drop_rules(sys_type):
  out =  ('# Reject\n' +
          '-A INPUT -j LREJECT\n' +
          '-A FORWARD -j LREJECT\n' +
          '-A OUTPUT -j LREJECT\n')

  if sys_type == 'CentOS':
    out += 'COMMIT\n'
    print_centos_rules(out)

  if sys_type == 'Debian':
    print_debian_rules(out)
#drop_rules


def smb_rules(inet, sys_type):
  out = ('# SMB Rules\n' +
         '-A INPUT -i '  + inet + ' -j SMB\n' +
         '-A OUTPUT -o ' + inet + ' -j SMB\n' +
         '-A INPUT -i '  + inet + ' -p tcp --dport 113 -j LREJECT\n' +
         '-A OUTPUT -o ' + inet + ' -p tcp --sport 113 -j LREJECT\n')

  if sys_type == 'CentOS':
    print_centos_rules(out)

  if sys_type == 'Debian':
    print_debian_rules(out)
#smb_rules


def icmp_rules(inet, sys_type):
  out = ('# ICMP Rules\n' +
         '-A INPUT -i '  + inet + ' -p icmp -j ICMPINBOUND\n' +
         '-A INPUT -i '  + inet + ' -p udp --dport 33434:33523 -j LDROP\n' +
         '-A OUTPUT -o ' + inet + ' -p icmp -j ICMPOUTBOUND\n' +
         '-A OUTPUT -o ' + inet + ' -p udp --dport 33434:33523 -j LDROP\n')

  if sys_type == 'CentOS':
    print_centos_rules(out)

  if sys_type == 'Debian':
    print_debian_rules(out)
#icmp_rules


def spoofing_rules(inet, sys_type):
  out = ('# Spoof rules\n' +
         '-A INPUT -i ' + inet + ' -s 127.0.0.0/8 -j DROP\n' +
         '-A INPUT -i ' + inet + ' -s 10.0.0.0/8 -j DROP\n' +
         '-A INPUT -i ' + inet + ' -s 169.254.0.0/16 -j DROP\n' +
         '-A INPUT -i ' + inet + ' -s 172.16.0.0/12 -j DROP\n' +
         '-A INPUT -i ' + inet + ' -s 224.0.0.0/4 -j DROP\n' +
         '-A INPUT -i ' + inet + ' -d 224.0.0.0/4 -j DROP\n' +
         '-A INPUT -i ' + inet + ' -s 240.0.0.0/5 -j DROP\n' +
         '-A INPUT -i ' + inet + ' -d 240.0.0.0/5 -j DROP\n' +
         '-A INPUT -i ' + inet + ' -s 0.0.0.0/8 -j DROP\n' +
         '-A INPUT -i ' + inet + ' -d 0.0.0.0/8 -j DROP\n' +
         '-A INPUT -i ' + inet + ' -d 239.255.255.0/24 -j DROP\n' +
         '-A INPUT -i ' + inet + ' -d 255.255.255.255 -j DROP\n')

  if sys_type == 'CentOS':
    print_centos_rules(out)

  if sys_type == 'Debian':
    print_debian_rules(out)
#spoofing_rules


def set_default_policy(conf):
  if conf['type'] == 'CentOS':
    print('# Default policy\n' +
          '*filter\n' +
          ':INPUT '   + conf['policy']['input']   + ' [0:0]\n' +
          ':FORWARD ' + conf['policy']['forward'] + ' [0:0]\n' +
          ':OUTPUT '  + conf['policy']['output']  + ' [0:0]')

  if conf['type'] == 'Debian':
    print('#!/bin/bash\n\n' +
          '# Flush rules\n' +
          '/sbin/iptables -F\n' +
          '/sbin/iptables -X\n' +
          '/sbin/iptables -Z\n\n' +
          '# Flush nat rules \n' +
          '/sbin/iptables -t nat -F\n' +
          '/sbin/iptables -t nat -X\n' +
          '/sbin/iptables -t nat -Z\n')

    print('# Default policy\n' +
          '/sbin/iptables -P INPUT '   + conf['policy']['input'] + '\n' +
          '/sbin/iptables -P FORWARD ' + conf['policy']['forward'] + '\n' +
          '/sbin/iptables -P OUTPUT '  + conf['policy']['output'])
#set_default_policy


def postrouting(conf):
  out = '# Postrouting\n'
  for cnf in conf['config']['inet']['internal']:
    out += ('-t nat -A POSTROUTING -s ' + cnf['range'] + ' -o ' +
            conf['config']['inet']['external']['name'] + ' -j MASQUERADE\n')

  if conf['config']['type'] == 'Debian':
    print_debian_rules(out)

  if conf['config']['type'] == 'CentOS':
    tmp = ('*nat\n' +
           ':PREROUTING ACCEPT [0:0]\n' +
           ':POSTROUTING ACCEPT [0:0]\n' +
           ':OUTPUT ACCEPT [0:0]\n')

    out = tmp + out + 'COMMIT'
    print_centos_rules(out)
#postrouting


def set_general_filter(conf):
  out = ('# General filter\n' +
         '-A INPUT -m conntrack --ctstate INVALID -j LINVALID\n' +
         '-A INPUT -p tcp -j CHECKBADFLAG\n' +
         '-A OUTPUT -m conntrack --ctstate INVALID -j LINVALID\n' +
         '-A OUTPUT -p tcp -j CHECKBADFLAG\n' +
         '-A FORWARD -m conntrack --ctstate INVALID -j LINVALID\n' +
         '-A FORWARD -p tcp -j CHECKBADFLAG\n' +
         '-A INPUT -i lo -j ACCEPT\n' +
         '-A OUTPUT -o lo -j ACCEPT\n')

  if conf['type'] == 'CentOS':
    print_centos_rules(out)

  if conf['type'] == 'Debian':
    print_debian_rules(out)
#set_general_filter

def chain_rules(conf):
  out = ('# Logging Chains\n\n' +
         '## Invalid packet\n' +
         '-N LINVALID\n' +
         '-A LINVALID -m limit --limit 2/s --limit-burst 10 ' +
                                '-j LOG --log-prefix "fp=INVALID:1 a=DROP "\n' +
         '-A LINVALID -j DROP\n' +
         '## TCP-packet with one or more bad flags\n' +
         '-N LBADFLAG\n' +
         '-A LBADFLAG -m limit --limit 2/s --limit-burst 10 ' +
                                '-j LOG --log-prefix "fp=BADFLAG:1 a=DROP "\n' +
         '-A LBADFLAG -j DROP\n' +
         '## Logging of connection attempts on special ports\n' +
         '-N LSPECIALPORT\n' +
         '-A LSPECIALPORT -m limit --limit 2/s --limit-burst 10 ' +
                            '-j LOG --log-prefix "fp=SPECIALPORT:1 a=DROP "\n' +
         '-A LSPECIALPORT -j DROP\n'
         '## Logging of possible TCP-SYN-Floods\n' +
         '-N LSYNFLOOD\n' +
         '-A LSYNFLOOD -m limit --limit 5/s --limit-burst 100 ' +
                               '-j LOG --log-prefix "fp=SYNFLOOD:1 a=DROP "\n' +
         '-A LSYNFLOOD -j DROP\n' +
         '## Logging of possible Ping-Floods\n' +
         '-N LPINGFLOOD\n' +
         '-A LPINGFLOOD -m limit --limit 2/s --limit-burst 10 ' +
                              '-j LOG --log-prefix "fp=PINGFLOOD:1 a=DROP "\n' +
         '-A LPINGFLOOD -j DROP\n' +
         '## All other dropped packets\n' +
         '-N LDROP\n' +
         '-A LDROP -p tcp -m limit --limit 2/s --limit-burst 10 ' +
                                    '-j LOG --log-prefix "fp=TCP:1 a=DROP "\n' +
         '-A LDROP -p udp -m limit --limit 2/s --limit-burst 10 ' +
                                    '-j LOG --log-prefix "fp=UDP:2 a=DROP "\n' +
         '-A LDROP -p icmp -m limit --limit 2/s --limit-burst 10 ' +
                                   '-j LOG --log-prefix "fp=ICMP:3 a=DROP "\n' +
         '-A LDROP -f -m limit --limit 2/s --limit-burst 10 ' +
                               '-j LOG --log-prefix "fp=FRAGMENT:4 a=DROP "\n' +
          '-A LDROP -j DROP\n' +
          '## All other rejected packets\n' +
          '-N LREJECT\n' +
          '-A LREJECT -p tcp -m limit --limit 2/s --limit-burst 10 ' +
                                  '-j LOG --log-prefix "fp=TCP:1 a=REJECT "\n' +
          '-A LREJECT -p udp -m limit --limit 2/s --limit-burst 10 ' +
                                  '-j LOG --log-prefix "fp=UDP:2 a=REJECT "\n' +
          '-A LREJECT -p icmp -m limit --limit 2/s --limit-burst 10 ' +
                                 '-j LOG --log-prefix "fp=ICMP:3 a=REJECT "\n' +
          '-A LREJECT -f -m limit --limit 2/s --limit-burst 10 ' +
                             '-j LOG --log-prefix "fp=FRAGMENT:4 a=REJECT "\n' +
          '-A LREJECT -p tcp -j REJECT --reject-with tcp-reset\n' +
          '-A LREJECT -p udp -j REJECT --reject-with icmp-port-unreachable\n' +
          '-A LREJECT -j REJECT\n' +
          '## TCPACCEPT\n' +
          '-N TCPACCEPT\n' +
          '-A TCPACCEPT -p tcp --syn -m limit --limit 5/s ' +
                                               '--limit-burst 100 -j ACCEPT\n' +
          '-A TCPACCEPT -p tcp --syn -j LSYNFLOOD\n' +
          '-A TCPACCEPT -p tcp ! --syn -j ACCEPT\n' +
          '## CHECKBADFLAG\n' +
          '-N CHECKBADFLAG\n' +
          '-A CHECKBADFLAG -p tcp --tcp-flags ALL FIN,URG,PSH -j LBADFLAG\n' +
          '-A CHECKBADFLAG -p tcp --tcp-flags ALL SYN,RST,ACK,FIN,URG ' +
                                                               '-j LBADFLAG\n' +
          '-A CHECKBADFLAG -p tcp --tcp-flags ALL ALL -j LBADFLAG\n' +
          '-A CHECKBADFLAG -p tcp --tcp-flags ALL NONE -j LBADFLAG\n' +
          '-A CHECKBADFLAG -p tcp --tcp-flags SYN,RST SYN,RST -j LBADFLAG\n' +
          '-A CHECKBADFLAG -p tcp --tcp-flags SYN,FIN SYN,FIN -j LBADFLAG\n' +
          '## SMB-Traffic\n' +
          '-N SMB\n' +
          '-A SMB -p tcp --dport 137 -j DROP\n' +
          '-A SMB -p tcp --dport 138 -j DROP\n' +
          '-A SMB -p tcp --dport 139 -j DROP\n' +
          '-A SMB -p tcp --dport 445 -j DROP\n' +
          '-A SMB -p udp --dport 137 -j DROP\n' +
          '-A SMB -p udp --dport 138 -j DROP\n' +
          '-A SMB -p udp --dport 139 -j DROP\n' +
          '-A SMB -p udp --dport 445 -j DROP\n' +
          '-A SMB -p tcp --sport 137 -j DROP\n' +
          '-A SMB -p tcp --sport 138 -j DROP\n' +
          '-A SMB -p tcp --sport 139 -j DROP\n' +
          '-A SMB -p tcp --sport 445 -j DROP\n' +
          '-A SMB -p udp --sport 137 -j DROP\n' +
          '-A SMB -p udp --sport 138 -j DROP\n' +
          '-A SMB -p udp --sport 139 -j DROP\n' +
          '-A SMB -p udp --sport 445 -j DROP\n' +
          '## ICMP-Traffic - Inbound ICMP/Traceroute\n' +
          '-N ICMPINBOUND\n' +
          '-A ICMPINBOUND -p icmp --icmp-type echo-request ' +
                           '-m limit --limit 5/s --limit-burst 10 -j ACCEPT\n' +
          '-A ICMPINBOUND -p icmp --icmp-type echo-request -j LPINGFLOOD\n'
          '-A ICMPINBOUND -p icmp --icmp-type redirect -j LDROP\n'
          '-A ICMPINBOUND -p icmp --icmp-type timestamp-request -j LDROP\n'
          '-A ICMPINBOUND -p icmp --icmp-type timestamp-reply -j LDROP\n'
          '-A ICMPINBOUND -p icmp --icmp-type address-mask-request -j LDROP\n'
          '-A ICMPINBOUND -p icmp --icmp-type address-mask-reply -j LDROP\n'
          '-A ICMPINBOUND -p icmp -j ACCEPT\n' +
          '## ICMP-Traffic - Outbound ICMP/Traceroute\n' +
          '-N ICMPOUTBOUND\n' +
          '-A ICMPOUTBOUND -p icmp --icmp-type redirect -j LDROP\n' +
          '-A ICMPOUTBOUND -p icmp --icmp-type ttl-zero-during-transit ' +
                                                                  '-j LDROP\n' +
          '-A ICMPOUTBOUND -p icmp --icmp-type ttl-zero-during-reassembly ' +
                                                                  '-j LDROP\n' +
          '-A ICMPOUTBOUND -p icmp --icmp-type parameter-problem -j LDROP\n' +
          '-A ICMPOUTBOUND -p icmp --icmp-type timestamp-request -j LDROP\n' +
          '-A ICMPOUTBOUND -p icmp --icmp-type timestamp-reply -j LDROP\n' +
          '-A ICMPOUTBOUND -p icmp --icmp-type address-mask-request -j LDROP\n' +
          '-A ICMPOUTBOUND -p icmp --icmp-type address-mask-reply -j LDROP\n' +
          '-A ICMPOUTBOUND -p icmp -j ACCEPT')

  if conf['type'] == 'CentOS':
    print_centos_rules(out)

  if conf['type'] == 'Debian':
    print_debian_rules(out)
#chain_rules


if __name__ == '__main__':
  try:
    sys.setdefaultencoding("utf8")
  except:
    reload(sys)
    sys.setdefaultencoding("utf8")

  main()

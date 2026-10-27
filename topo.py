#!/usr/bin/env python3
"""Base topology: 3 hosts, 1 switch, 10 Mbps links with 5 ms delay."""
from mininet.net import Mininet
from mininet.node import OVSBridge
from mininet.link import TCLink
from mininet.log import setLogLevel

BW_MBPS = 10
DELAY = '5ms'

def build():
    net = Mininet(switch=OVSBridge, link=TCLink, controller=None)
    s1 = net.addSwitch('s1')
    for i in (1, 2, 3):
        h = net.addHost(f'h{i}', ip=f'10.0.0.{i}/24')
        net.addLink(h, s1, bw=BW_MBPS, delay=DELAY)
    return net

if __name__ == '__main__':
    setLogLevel('info')
    net = build()
    net.start()
    net.pingAll()
    net.stop()

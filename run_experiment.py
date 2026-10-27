#!/usr/bin/env python3
"""Run 3 traffic types h1 -> h2 and capture each on h2. Output goes to data/."""
import os, time
from topo import build

DATA = 'data'
SERVER_IP = '10.0.0.2'

def capture(h2, name, run_traffic):
    pcap = f'{DATA}/{name}.pcap'
    # start tcpdump in the background on h2 and remember its PID
    pid = h2.cmd(f'tcpdump -i h2-eth0 -U -w {pcap} >/dev/null 2>&1 & echo $!').strip()
    time.sleep(1)                     # let tcpdump start
    output = run_traffic()
    time.sleep(1)                     # let the last packets arrive
    h2.cmd(f'kill {pid}')
    time.sleep(1)                     # let tcpdump flush the file
    with open(f'{DATA}/{name}.log', 'w') as f:
        f.write(output)
    print(f'[done] {name}')

if __name__ == '__main__':
    os.makedirs(DATA, exist_ok=True)
    net = build()
    net.start()
    h1, h2 = net.get('h1'), net.get('h2')
    h2.cmd('iperf3 -s -D')            # iperf3 server as a daemon on h2

    capture(h2, 'icmp', lambda: h1.cmd(f'ping -c 100 -i 0.2 {SERVER_IP}'))
    capture(h2, 'tcp',  lambda: h1.cmd(f'iperf3 -c {SERVER_IP} -t 10'))
    capture(h2, 'udp',  lambda: h1.cmd(f'iperf3 -c {SERVER_IP} -u -b 5M -t 10'))

    h2.cmd('pkill iperf3')
    net.stop()

    # files were created by root; give them back to your user
    uid, gid = int(os.environ.get('SUDO_UID', 0)), int(os.environ.get('SUDO_GID', 0))
    for fn in os.listdir(DATA):
        os.chown(f'{DATA}/{fn}', uid, gid)

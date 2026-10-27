#!/usr/bin/env python3
"""Run REPEATS rounds of 3 traffic types h1 -> h2, capturing each on h2.
Output: data/runs/<type>_run<k>.pcap and .log. No randomness used."""
import os, subprocess, time
from topo import build

DATA = 'data/runs'
SERVER_IP = '10.0.0.2'
REPEATS = 5
DURATION = 10        # seconds per iperf3 test
PING_COUNT = 100

def capture(h2, name, run_traffic):
    pcap = f'{DATA}/{name}.pcap'
    # popen gives a real process handle, so we can wait for tcpdump to exit
    dump = h2.popen(['tcpdump', '-i', 'h2-eth0', '-U', '-w', pcap],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)                      # let tcpdump start
    output = run_traffic()
    time.sleep(1)                      # let last packets arrive
    dump.terminate()
    dump.wait(timeout=10)              # blocks until tcpdump has really stopped
    with open(f'{DATA}/{name}.log', 'w') as f:
        f.write(output)
    print(f'[done] {name}')

if __name__ == '__main__':
    os.makedirs(DATA, exist_ok=True)
    for k in range(1, REPEATS + 1):
        net = build()                  # fresh network each repeat
        net.start()
        h1, h2 = net.get('h1'), net.get('h2')
        h2.cmd('iperf3 -s -D')
        time.sleep(1)
        capture(h2, f'icmp_run{k}', lambda: h1.cmd(f'ping -c {PING_COUNT} -i 0.2 {SERVER_IP}'))
        capture(h2, f'tcp_run{k}',  lambda: h1.cmd(f'iperf3 -c {SERVER_IP} -t {DURATION}'))
        capture(h2, f'udp_run{k}',  lambda: h1.cmd(f'iperf3 -c {SERVER_IP} -u -b 5M -t {DURATION}'))
        h2.cmd('pkill iperf3')
        net.stop()
        print(f'=== run {k} of {REPEATS} finished')

    # hand ownership back to your normal user (we ran under sudo)
    uid, gid = int(os.environ.get('SUDO_UID', 0)), int(os.environ.get('SUDO_GID', 0))
    os.chown('data', uid, gid)
    for root, dirs, files in os.walk('data'):
        for n in dirs + files:
            os.chown(os.path.join(root, n), uid, gid)

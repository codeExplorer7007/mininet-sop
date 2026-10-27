#!/usr/bin/env python3
"""Median and max gap between ICMP echo requests in each icmp run."""
from scapy.all import rdpcap, ICMP, IP
for k in range(1, 6):
    p = [x for x in rdpcap(f'data/runs/icmp_run{k}.pcap') if IP in x and ICMP in x and x[ICMP].type == 8]
    t = [float(x.time) for x in p]
    g = sorted(round(1000 * (b - a)) for a, b in zip(t, t[1:]))
    print(f'run{k}: median {g[len(g)//2]} ms, max {g[-1]} ms')

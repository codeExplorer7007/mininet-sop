#!/usr/bin/env python3
"""Turn each pcap in data/ into per-flow features. Writes data/features.csv.
A flow = unidirectional 5-tuple (src, dst, sport, dport, protocol)."""
import csv, glob, os, statistics as st
from scapy.all import PcapReader, IP, TCP, UDP

PROTO = {1: 'ICMP', 6: 'TCP', 17: 'UDP'}
FIELDS = ['traffic', 'src', 'dst', 'sport', 'dport', 'proto', 'packets',
          'bytes', 'mean_size', 'std_size', 'max_size', 'duration_s',
          'mean_iat_ms', 'pkts_per_s', 'bytes_per_s']

def flow_key(pkt):
    ip = pkt[IP]
    if TCP in pkt:
        sport, dport = pkt[TCP].sport, pkt[TCP].dport
    elif UDP in pkt:
        sport, dport = pkt[UDP].sport, pkt[UDP].dport
    else:
        sport = dport = 0          # ICMP has no ports
    return (ip.src, ip.dst, sport, dport, PROTO.get(ip.proto, str(ip.proto)))

def extract(pcap_path):
    flows = {}
    reader = PcapReader(pcap_path)
    for pkt in reader:
        if IP not in pkt:          # skips ARP
            continue
        flows.setdefault(flow_key(pkt), []).append((float(pkt.time), len(pkt)))
    reader.close()

    traffic = os.path.splitext(os.path.basename(pcap_path))[0]
    rows = []
    for (src, dst, sport, dport, proto), pk in flows.items():
        times = [t for t, _ in pk]
        sizes = [s for _, s in pk]
        iats = [b - a for a, b in zip(times, times[1:])]
        dur = times[-1] - times[0]
        rows.append({
            'traffic': traffic, 'src': src, 'dst': dst,
            'sport': sport, 'dport': dport, 'proto': proto,
            'packets': len(pk), 'bytes': sum(sizes),
            'mean_size': round(st.mean(sizes), 1),
            'std_size': round(st.pstdev(sizes), 1),
            'max_size': max(sizes),
            'duration_s': round(dur, 3),
            'mean_iat_ms': round(1000 * st.mean(iats), 3) if iats else 0,
            'pkts_per_s': round(len(pk) / dur, 1) if dur > 0 else 0,
            'bytes_per_s': round(sum(sizes) / dur) if dur > 0 else 0,
        })
    return sorted(rows, key=lambda r: -r['packets'])

if __name__ == '__main__':
    all_rows = []
    for path in sorted(glob.glob('data/*.pcap')):
        all_rows += extract(path)
    with open('data/features.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(all_rows)
    print(f"{'traffic':8}{'src':>10}{'dst':>10}{'sport':>7}{'dport':>7}{'proto':>6}"
          f"{'pkts':>7}{'mean_sz':>9}{'max_sz':>8}{'dur_s':>8}{'iat_ms':>9}")
    for r in all_rows:
        print(f"{r['traffic']:8}{r['src']:>10}{r['dst']:>10}{r['sport']:>7}"
              f"{r['dport']:>7}{r['proto']:>6}{r['packets']:>7}{r['mean_size']:>9}"
              f"{r['max_size']:>8}{r['duration_s']:>8}{r['mean_iat_ms']:>9}")

#!/usr/bin/env python3
"""Per-flow features for every pcap in data/runs, a per-traffic summary
(mean and std over runs) and a plot. Flow = unidirectional 5-tuple."""
import csv, glob, os, re, statistics as st
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scapy.all import PcapReader, IP, TCP, UDP

PROTO = {1: 'ICMP', 6: 'TCP', 17: 'UDP'}
EXPECTED = {'icmp': 'ICMP', 'tcp': 'TCP', 'udp': 'UDP'}
CLIENT = '10.0.0.1'
FIELDS = ['traffic', 'run', 'src', 'dst', 'sport', 'dport', 'proto', 'packets',
          'bytes', 'mean_size', 'std_size', 'max_size', 'duration_s',
          'mean_iat_ms', 'pkts_per_s', 'bytes_per_s']
METRICS = ['packets', 'mean_size', 'mean_iat_ms', 'duration_s', 'bytes_per_s']

def flow_key(pkt):
    ip = pkt[IP]
    if TCP in pkt:
        sport, dport = pkt[TCP].sport, pkt[TCP].dport
    elif UDP in pkt:
        sport, dport = pkt[UDP].sport, pkt[UDP].dport
    else:
        sport = dport = 0
    return (ip.src, ip.dst, sport, dport, PROTO.get(ip.proto, str(ip.proto)))

def extract(path):
    m = re.match(r'(\w+?)_run(\d+)\.pcap', os.path.basename(path))
    traffic, run = m.group(1), int(m.group(2))
    flows = {}
    reader = PcapReader(path)
    for pkt in reader:
        if IP not in pkt:                 # skip ARP
            continue
        flows.setdefault(flow_key(pkt), []).append((float(pkt.time), len(pkt)))
    reader.close()
    rows = []
    for (src, dst, sport, dport, proto), pk in flows.items():
        t = [a for a, _ in pk]
        s = [b for _, b in pk]
        iats = [y - x for x, y in zip(t, t[1:])]
        dur = t[-1] - t[0]
        rows.append({
            'traffic': traffic, 'run': run, 'src': src, 'dst': dst,
            'sport': sport, 'dport': dport, 'proto': proto,
            'packets': len(pk), 'bytes': sum(s),
            'mean_size': round(st.mean(s), 1), 'std_size': round(st.pstdev(s), 1),
            'max_size': max(s), 'duration_s': round(dur, 3),
            'mean_iat_ms': round(1000 * st.mean(iats), 3) if iats else 0,
            'pkts_per_s': round(len(pk) / dur, 1) if dur > 0 else 0,
            'bytes_per_s': round(sum(s) / dur) if dur > 0 else 0})
    return rows

def main_flow(rows):
    """The client->server flow with the most packets and the expected protocol."""
    c = [r for r in rows if r['src'] == CLIENT and r['proto'] == EXPECTED[r['traffic']]]
    return max(c, key=lambda r: r['packets'])

if __name__ == '__main__':
    all_rows, mains = [], {}
    for path in sorted(glob.glob('data/runs/*.pcap')):
        rows = extract(path)
        all_rows += rows
        for r in rows:                    # contamination check
            if r['proto'] != EXPECTED[r['traffic']] and r['packets'] > 50:
                print(f"WARNING: {path} holds a large {r['proto']} flow: {r}")
        mains.setdefault(rows[0]['traffic'], []).append(main_flow(rows))

    with open('data/features.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(all_rows)

    summary = {}
    print(f"\n{'traffic':8}{'runs':>5}" + ''.join(f'{m:>22}' for m in METRICS))
    for tr in ('icmp', 'tcp', 'udp'):
        summary[tr] = {}
        line = f'{tr:8}{len(mains[tr]):>5}'
        for m in METRICS:
            v = [r[m] for r in mains[tr]]
            mu = st.mean(v)
            sd = st.stdev(v) if len(v) > 1 else 0
            summary[tr][m] = (mu, sd)
            line += f'{mu:>14.1f} +-{sd:>5.1f}'
        print(line)
    with open('data/summary.csv', 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['traffic'] + [f'{m}_{s}' for m in METRICS for s in ('mean', 'std')])
        for tr in summary:
            w.writerow([tr] + [round(x, 3) for m in METRICS for x in summary[tr][m]])

    # plot: mean over runs, error bars = std over runs
    names = list(summary)
    panels = [('mean_size', 'Mean packet size (bytes)', False),
              ('mean_iat_ms', 'Mean inter-arrival time (ms, log)', True),
              ('bytes_per_s', 'Rate (Mbit/s)', False)]
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8))
    for ax, (m, label, log) in zip(axes, panels):
        k = 8 / 1e6 if m == 'bytes_per_s' else 1
        ax.bar(names, [summary[n][m][0] * k for n in names],
               yerr=[summary[n][m][1] * k for n in names], capsize=4)
        ax.set_title(label, fontsize=10)
        if log:
            ax.set_yscale('log')
    fig.suptitle('Main client-to-server flow per traffic type (mean of 5 runs, bars = std)')
    fig.tight_layout()
    fig.savefig('data/features_plot.png', dpi=150)
    print('\nWrote data/features.csv, data/summary.csv, data/features_plot.png')

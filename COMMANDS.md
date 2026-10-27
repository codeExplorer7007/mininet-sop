# COMMANDS.md

Exact commands run during the project, in order. Everything below was run inside an Ubuntu 26.04.1 LTS VM (VirtualBox on Windows) in the Terminal.
Seed: no randomness is used, so no seed applies.

## 0. VM setup (Windows host, VirtualBox GUI)
- Installed VirtualBox; the optional Extension Pack failed with a version mismatch and was skipped (not needed).
- Created VM `mininet-ubuntu`: 4 GB RAM, 4 CPUs, 25 GB disk, ISO `ubuntu-26.04.1-desktop-amd64.iso`, "Skip Unattended Installation" ticked.
- Installed Ubuntu with "Install Ubuntu" and "Erase disk" (virtual disk only), no third-party software.

## 1. Git and GitHub
```bash
sudo apt update
sudo apt install -y git gh
git config --global user.name "Your Name"
git config --global user.email "your-github-email@example.com"
gh auth login          # GitHub.com -> HTTPS -> Yes -> Login with a web browser
git clone https://github.com/codeExplorer7007/mininet-sop.git
cd mininet-sop
```

## 2. Install tools
```bash
sudo apt update
sudo apt install -y mininet iperf3 tcpdump wireshark python3-scapy python3-pandas
sudo mn --test pingall          # result: 0% dropped (2/2 received)
```
(The first attempt failed with "Unable to locate package python3-pandas~" because of a stray `~` typed at the end; retyping without it fixed it.)

## 3. Base topology
```bash
nano topo.py
sudo python3 topo.py            # result: 0% dropped (6/6 received)
git add topo.py
git commit -m "Added base topology (3 hosts, 10 Mbps, 5ms delay)"
git push
```

## 4. Pilot run (single run, later found contaminated)
```bash
nano run_experiment.py          # first version: one run per traffic type
sudo python3 run_experiment.py
ls -lh data/
head -20 data/tcp.log
head -20 data/udp.log
head -20 data/icmp.log
git add run_experiment.py data/
git commit -m "Added an experiment runner that captures for ICMP, TCP and UDP."
git push
```

## 5. First feature extraction (found the contamination)
```bash
nano features.py
python3 features.py                          # PermissionError: data/ was root-owned
sudo chown -R $USER:$USER data
python3 features.py                          # table showed UDP packets inside tcp.pcap
git add features.py data/features.csv
git commit -m "Added per-flow feature extraction and features.csv"
git push
```

## 6. Move contaminated pilot data aside
```bash
mkdir -p data/pilot
git mv data/*.pcap data/*.log data/features.csv data/pilot/
git commit -m "Moved contaminated single-run data to data/pilot"
git push
```

## 7. Fixed runner (5 repeats) and new feature script
```bash
sudo apt install -y python3-matplotlib
nano run_experiment.py          # tcpdump started with popen, waited on exit; REPEATS = 5
nano features.py                # per-run summary, contamination warning, plot
sudo python3 features.py        # mistake: ran too early, empty data/runs -> KeyError 'icmp'
sudo python3 run_experiment.py  # mistake: suspended with Ctrl+Z
sudo python3 run_experiment.py  # RTNETLINK answers: File exists (stale interfaces)
```

## 8. Cleanup after the stuck run
```bash
sudo pkill -9 -f run_experiment.py
sudo pkill tcpdump
sudo pkill iperf3
sudo mn -c
sudo chown -R $USER:$USER data
jobs
kill %1                          # stray stopped `cat` job
```

## 9. Final experiment
```bash
sudo python3 -u run_experiment.py | tee data/run_log.txt
ls data/runs | wc -l             # 30
python3 features.py              # no WARNING lines
```

## 10. Commit final data
```bash
git add data/runs data/run_log.txt data/features.csv data/summary.csv data/features_plot.png
git commit -m "Add 5-run captures, summary table and plot"
git push
```

## 11. Screenshots and report (fill in as you go)
```bash
wireshark data/runs/icmp_run1.pcap &
wireshark data/runs/tcp_run1.pcap &
wireshark data/runs/udp_run1.pcap &
git add screenshots
git commit -m "Add Wireshark and terminal screenshots"
cd report
pdflatex report.tex
cd ..
git add report COMMANDS.md NOTES.md
git commit -m "Add report, commands and notes"
git push
```

# NOTES.md: where I got stuck and how I fixed it

1. **VirtualBox Extension Pack error (VERR_VERSION_MISMATCH, expected 7.2 got 7.1).**
   The pack version did not match VirtualBox. The pack is optional and not needed for Mininet, so I skipped it.

2. **`PermissionError` writing `data/features.csv`.**
   The runner used `sudo`, so `data/` was owned by root. Fixed with `sudo chown -R $USER:$USER data`, and the runner now chowns the folder and files after running.

3. **TCP capture contained UDP packets (found from the features table).**
   In the first single-run data, `tcp.pcap` held a UDP flow with the same port and packet count as `udp.pcap` (4318 packets), and the file was 17 MB. The tcpdump from the TCP step was still running during the UDP test. Fix: start tcpdump with `popen` and wait for it to exit before the next test, add a contamination warning to `features.py`, and repeat the experiment 5 times. The bad data is kept in `data/pilot/` for transparency.

4. **`RTNETLINK answers: File exists` when starting Mininet.**
   I had suspended a running experiment with Ctrl+Z, which left stale virtual interfaces. Fixed with `sudo mn -c` after killing the leftover processes. Use Ctrl+C to stop, never Ctrl+Z.

5. **Unexplained observations (not fixed).**
   ICMP requests were meant to be 200 ms apart. Per-run median gaps were 207-282 ms, with stalls up to 702-1244 ms in every run, which inflates the mean IAT to about 306 ms. I did not find the cause. TCP throughput also varied between 5 and 14 Mbit/s per interval on a 10 Mbit/s link, also unexplained. Both are listed as limitations in the report.

#!/bin/bash
set -e
cd /tmp
rm -rf brutvm
git clone https://github.com/eyescares/brutvm.git
cd brutvm
pip3 install aiohttp -q
curl -sL "https://github.com/brannondorsey/naive-hashcat/releases/download/data/rockyou.txt" -o rockyou_full.txt
echo "[*] Ready. Run: cd /tmp/brutvm && python3 -u brut.py"

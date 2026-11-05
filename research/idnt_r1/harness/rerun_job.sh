#!/bin/bash
# IDNT-R1 rerun of the 6 benches whose top was misselected by the harness in regress-job-01.
set -u
cd "$(dirname "$0")/../.."
export PATH=/home/john/.local/opt/oss-cad-suite-20261027/bin:/usr/local/bin:/usr/bin:/bin
exec /usr/bin/python3 build/idnt-r1/run_benches.py . - build/idnt-r1/rerun_list.txt build/idnt-r1/rerun-benches

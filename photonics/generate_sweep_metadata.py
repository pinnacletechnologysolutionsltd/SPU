#!/usr/bin/env python3
"""
Generate metadata JSON for completed sweep CSVs to allow reproducible replay.

Usage: edit the RUNS list below to point at CSV, num_trials, master_seed and description.
The script writes {csv}.metadata.json next to each CSV.
"""
import os, csv, json, math

ROOT = os.path.dirname(__file__)
RUNS = [
    {
        'csv': os.path.join(ROOT, 'results', 'sweeps', 'calib_amp_det_combined_full.csv'),
        'num_trials': 16000,
        'master_seed': 13,
        'description': 'calibration-error × sigma_amp × detector_noise combined sweep (Full)'
    },
    {
        'csv': os.path.join(ROOT, 'results', 'sweeps', 'deltaT_sweep_full.csv'),
        'num_trials': 16000,
        'master_seed': 13,
        'description': 'deltaT sweep (C2) default params'
    },
    {
        'csv': os.path.join(ROOT, 'results', 'sweeps', 'deltaT_calib_sweep_full.csv'),
        'num_trials': 16000,
        'master_seed': 13,
        'description': 'deltaT × calibration-error sweep (Full)'
    }
]

for run in RUNS:
    csvpath = run['csv']
    if not os.path.exists(csvpath):
        print('Missing CSV, skipping:', csvpath)
        continue
    meta = {
        'csv': os.path.relpath(csvpath, ROOT),
        'num_trials': run['num_trials'],
        'master_seed': run['master_seed'],
        'description': run.get('description',''),
        'cells': []
    }
    with open(csvpath, 'r') as f:
        r = csv.reader(f)
        header = next(r)
        cell_index = 0
        for row in r:
            # store the parsed row as params; keep original header mapping
            rowdict = {}
            for k, v in zip(header, row):
                # try to convert to number
                try:
                    if '.' in v or 'e' in v.lower():
                        val = float(v)
                    else:
                        val = int(v)
                except Exception:
                    val = v
                rowdict[k] = val
            # compute start_global_trial index so trials can be reproduced
            start_global_trial = cell_index * run['num_trials']
            rowdict['_cell_index'] = cell_index
            rowdict['_start_global_trial'] = start_global_trial
            meta['cells'].append(rowdict)
            cell_index += 1
    metafile = csvpath + '.metadata.json'
    with open(metafile, 'w') as mf:
        json.dump(meta, mf, indent=2)
    print('Wrote metadata:', metafile)

print('Done')

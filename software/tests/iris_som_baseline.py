#!/usr/bin/env python3
"""
iris_som_baseline.py — Iris Dataset SOM Accuracy Baseline

Downloads the standard Iris dataset, trains a 64-node SOM using the Python
exact rational oracle, and computes the clustering accuracy.
"""

import sys
import os
import csv
import urllib.request
import random
from collections import Counter

sys.path.insert(0, 'software/lib')
try:
    from rational_som import RationalSurd as RS, rs, SomNode, find_bmu, hex_neighbors
except ImportError:
    print("Error: rational_som.py not found. Run from repo root.")
    sys.exit(1)

IRIS_URL = "https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data"
DATA_DIR = "software/tests/data"
IRIS_FILE = os.path.join(DATA_DIR, "iris.csv")

def ensure_dataset():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    if not os.path.exists(IRIS_FILE):
        print(f"Downloading Iris dataset to {IRIS_FILE}...")
        urllib.request.urlretrieve(IRIS_URL, IRIS_FILE)

def load_dataset():
    ensure_dataset()
    features = []
    labels = []
    label_map = {"Iris-setosa": 0, "Iris-versicolor": 1, "Iris-virginica": 2}
    
    with open(IRIS_FILE, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 5:
                continue
            # Multiply by 10 to convert e.g. 5.1 to integer 51 for exact rational math
            f_vec = [rs(int(float(x) * 10)) for x in row[:4]]
            features.append(f_vec)
            labels.append(label_map.get(row[4], -1))
    return features, labels

def init_nodes(num_nodes=64):
    """Initialize an 8x8 hexagonal grid of nodes with random small weights."""
    nodes = []
    # Iris features (scaled x10) ranges roughly:
    # Sepal Length: 43 - 79
    # Sepal Width: 20 - 44
    # Petal Length: 10 - 69
    # Petal Width: 1 - 25
    
    for i in range(num_nodes):
        q = i % 8
        r = i // 8
        # Start weights distributed roughly in the feature space
        w = (
            rs(random.randint(40, 80)),
            rs(random.randint(20, 45)),
            rs(random.randint(10, 70)),
            rs(random.randint(0, 30))
        )
        nodes.append(SomNode(i, q, r, i, w, True))
    return nodes

def oracle_train_epoch(nodes, inputs, shift, feature_weights, neighborhood_radius=1):
    """One epoch of training, updating BMU and neighbors."""
    new_nodes = list(nodes)
    changed = False
    
    # Precompute grid neighbors for fast lookup
    node_by_qr = {(n.axial_q, n.axial_r): n for n in nodes}
    
    for x in inputs:
        result = find_bmu(x, new_nodes, feature_weights)
        if not result.valid: 
            continue
        
        bmu_id = result.best_node_id
        bmu_node = new_nodes[bmu_id]
        
        # Determine neighborhood (radius 1: BMU + hex_neighbors)
        update_targets = [bmu_id]
        if neighborhood_radius > 0:
            for dq, dr in hex_neighbors(bmu_node.axial_q, bmu_node.axial_r):
                neighbor = node_by_qr.get((bmu_node.axial_q + dq, bmu_node.axial_r + dr))
                if neighbor:
                    update_targets.append(neighbor.node_id)
        
        # Apply dyadic update to BMU and neighbors
        for target_id in update_targets:
            w = list(new_nodes[target_id].weights)
            new_w = []
            for w_j, x_j in zip(w, x):
                delta = x_j - w_j
                # Arithmetic right shift logic
                update = RS(delta.p >> shift, delta.q >> shift)
                new_w.append(w_j + update)
                
            if tuple(new_w) != tuple(w):
                changed = True
                new_nodes[target_id] = SomNode(
                    node_id=target_id,
                    axial_q=new_nodes[target_id].axial_q,
                    axial_r=new_nodes[target_id].axial_r,
                    cluster_label=new_nodes[target_id].cluster_label,
                    weights=tuple(new_w),
                    valid=True
                )
    return changed, new_nodes

def evaluate_accuracy(nodes, features, labels, feature_weights):
    """
    Evaluate unsupervised clustering accuracy.
    Maps each SOM node to the majority class of the samples that map to it.
    """
    node_to_class_counts = {n.node_id: Counter() for n in nodes}
    
    # 1. Assign each sample to its BMU
    sample_bmu = []
    for x, y in zip(features, labels):
        result = find_bmu(x, nodes, feature_weights)
        if result.valid:
            bmu = result.best_node_id
            node_to_class_counts[bmu][y] += 1
            sample_bmu.append(bmu)
        else:
            sample_bmu.append(-1)
            
    # 2. Assign majority class to each node
    node_majority_class = {}
    for node_id, counts in node_to_class_counts.items():
        if counts:
            majority_class = counts.most_common(1)[0][0]
            node_majority_class[node_id] = majority_class
        else:
            node_majority_class[node_id] = -1 # No samples mapped here
            
    # 3. Compute accuracy
    correct = 0
    total = len(features)
    for bmu, y in zip(sample_bmu, labels):
        if bmu != -1 and node_majority_class[bmu] == y:
            correct += 1
            
    return correct / total if total > 0 else 0

def export_mem_file(nodes, filename="build/iris_som_weights.mem"):
    """
    Export node weights to a .mem file for Verilog $readmemh.
    Each node is 144 bits: 4 features * 2 components (P,Q) * 18 bits.
    Format: [F3_Q F3_P F2_Q F2_P F1_Q F1_P F0_Q F0_P]
    """
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w') as f:
        f.write("// Iris SOM 64-Node Weights (144-bit packed)\n")
        f.write("// Format: {F3_Q[17:0], F3_P[17:0], ..., F0_Q[17:0], F0_P[17:0]}\n")
        for node in nodes:
            val = 0
            for i, w in enumerate(node.weights):
                p = w.p & 0x3FFFF
                q = w.q & 0x3FFFF
                val |= (p << (i * 36))
                val |= (q << (i * 36 + 18))
            f.write(f"{val:036x}\n")
    print(f"   Saved .mem file to {filename}")

def export_bin_file(nodes, filename="build/iris_som_weights.bin"):
    """
    Export node weights to a .bin file for SD card hydration (via spu_sd_inhaler).
    Each node (144 bits) is zero-padded to 192 bits (24 bytes = exactly three 64-bit chords).
    Big-endian format to match spu_sd_inhaler's chord assembly.
    """
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'wb') as f:
        for node in nodes:
            val = 0
            for i, w in enumerate(node.weights):
                p = w.p & 0x3FFFF
                q = w.q & 0x3FFFF
                val |= (p << (i * 36))
                val |= (q << (i * 36 + 18))
            f.write(val.to_bytes(24, byteorder='big'))
    print(f"   Saved .bin file to {filename}")

def main():
    print("=== SOM Iris Accuracy Baseline ===")
    
    random.seed(42) # For reproducible initialization
    
    print("1. Loading Dataset...")
    features, labels = load_dataset()
    print(f"   Loaded {len(features)} samples.")
    
    print("2. Initializing 64-Node SOM...")
    nodes = init_nodes(64)
    feature_weights = [rs(1), rs(1), rs(1), rs(1)]
    
    # Shuffling inputs for training
    dataset = list(zip(features, labels))
    random.shuffle(dataset)
    train_features = [f for f, l in dataset]
    
    print("3. Training (15 Epochs)...")
    shifts = [1]*3 + [2]*4 + [3]*4 + [4]*4
    
    for epoch, shift in enumerate(shifts):
        # Neighborhood radius decreases over time
        radius = 1 if epoch < 7 else 0
        
        changed, nodes = oracle_train_epoch(nodes, train_features, shift, feature_weights, neighborhood_radius=radius)
        acc = evaluate_accuracy(nodes, train_features, labels, feature_weights)
        
        print(f"   Epoch {epoch+1:2d} (shift={shift}, rad={radius}): Accuracy = {acc*100:.2f}% {'[Stable]' if not changed else ''}")
        
        # Shuffle for next epoch
        random.shuffle(train_features)
        
    print("\nFinal Accuracy Evaluation...")
    final_acc = evaluate_accuracy(nodes, features, labels, feature_weights)
    print(f"Overall Clustering Accuracy: {final_acc*100:.2f}%")
    
    print("\n4. Exporting Weights...")
    export_mem_file(nodes)
    export_bin_file(nodes)
    
if __name__ == '__main__':
    main()

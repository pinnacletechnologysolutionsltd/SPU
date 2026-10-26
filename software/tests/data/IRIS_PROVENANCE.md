# Iris Dataset — Provenance and Attribution

**Local dataset:** `iris.csv`

**Recorded SHA-256:** `6f608b71a7317216319b4d27b4d9bc84e6abd734eda7872b71a458569e2656c0`

**Upstream dataset:** Iris, UCI Machine Learning Repository, dataset 53.

**Recommended citation:**

Fisher, R. (1936). *Iris [Dataset].* UCI Machine Learning Repository. https://doi.org/10.24432/C56C76

**Upstream license:** Creative Commons Attribution 4.0 International (CC BY 4.0).

https://creativecommons.org/licenses/by/4.0/

The UCI repository permits redistribution and adaptation with appropriate attribution and identification of modifications.

### Dataset identity

This file is used as an Iris test corpus within the SPU software and hardware evaluation suite.

The UCI repository identifies differences between its distributed data and the data presented in Fisher's original paper, including the 35th and 38th samples.

Comparison performed 2026-10-21 against the files in UCI's `iris.zip` (dataset 53): `iris.csv` is **byte-identical to UCI's `iris.data`**
(same SHA-256, 150 rows, no scaling, reformatting or correction). It differs from UCI's `bezdekIris.data` at samples 35 and 38 only. It therefore carries
UCI's `iris.data` values for those two samples, not the corrected values.

### Redistribution

The upstream dataset's CC BY 4.0 license applies to the dataset and its adaptations, not automatically to the SPU software, RTL, or other repository content.

This notice is intended to preserve attribution and provenance alongside the redistributed dataset.

**Verification status:** Upstream license and citation confirmed (as listed on the UCI dataset page); local file verified identical to UCI `iris.data`; no transformations.

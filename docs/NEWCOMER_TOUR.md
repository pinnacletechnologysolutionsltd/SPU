# Guided tour: exact geometry in SPU

This short tour introduces the project through two interactive geometry lessons.
The pages are hosted with the SPU documentation, so the browser demonstrations
need no local build, FPGA, or simulator. They are teaching examples; browser
execution is not an SPU instruction or hardware run.

## 1. What the project does

Read [Exact arithmetic, explained](START_HERE.md) for the project’s scope,
current claims, and evidence boundaries. SPU explores exact arithmetic and
geometric computation in software and on FPGAs. The examples below show the
mathematics; they do not imply that every operation is implemented in hardware.

## 2. Move a point in Quadray coordinates

Open [Baby’s First Quadray](demos/baby-quadray.html).

1. Change one of the A, B, C, or D controls and watch the point move.
2. Predict what **Add common +1** will do, then try it. All four numbers change,
   while the represented point stays fixed. The four-coordinate description
   has one common-offset redundancy, leaving three independent coordinates.
3. Select the proper rotation and then the reflection. Compare the displayed
   orientation signs: a coordinate permutation is not automatically a spatial
   rotation.

The exact coordinate arithmetic and the SVG display are separate parts of the
lesson. The browser performs the demonstration; it does not call the SPU
simulator or FPGA.

## 3. Explore golden geometry

Open [One exact golden-ratio icosahedron](demos/icosahedron_phi.html).
Select vertices and change the carried structure to see how labels or weights
restrict the symmetries that preserve it. The lesson distinguishes the
unlabelled solid’s geometry from extra structure placed on its vertices. Its
screen projection is approximate; the visible image is not a geometric proof.

The [seed dynamics page](demos/gc5b_seed_dynamics.html) is an optional research
visualization. It displays a small, frozen software experiment and is not a
general claim about aperiodic dynamics or physical chirality.

## 4. Continue with the software and GPU material

- [Your first hour](FIRST_HOUR.md) introduces the software tools and programs.
- [Quadray for programmers](QUADRAY_FOR_PROGRAMMERS.md) gives a more detailed
  coordinate and transformation explanation.
- [Hardware-free demo tour](DEMO_TOUR.md) describes existing software
  demonstrations and their evidence scope.
- [Software guide](software_guide.md) documents commands that run from a
  repository checkout.
- [Hardware evidence ledger](hardware_evidence.md) records physical FPGA
  demonstrations separately from browser and software results.

The standalone SIM-1 program is a C++ software renderer that runs on the host
CPU. It is distinct from both these browser pages and the Python T1d device
model. See the [software guide](software_guide.md) and SIM-1’s own repository
documentation for their separate supported commands. A clean-checkout,
cross-repository scene workflow is still pending; this tour does not claim one.

## Demo source and scope

The published pages are self-contained browser examples copied from the
corresponding `examples/` source files. See [demo provenance](demos/DEMO_PROVENANCE.md).
They aid explanation and exploration; qualification claims remain tied to the
source tests and evidence records linked from the relevant project documents.

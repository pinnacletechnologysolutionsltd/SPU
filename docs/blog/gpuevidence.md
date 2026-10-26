VGA Test Pattern to Depth-Resolved Triangles

This is a clear draft. I’ve tightened the signal path and clarified an important evidence boundary: the September 4 colour bars proved the VGA display path; the triangle and depth results came in separate demonstrations. I’ve also tied the 246 LUTs and 54 flip-flops specifically to the colour-bar implementation, not the later GPU.

GPU: First Display Evidence

The first image from the project was a VGA test pattern: eight colour bars and a moving marker. It was not yet a GPU demonstration. Over the next two days, the work progressed from a single rasterized triangle to two overlapping triangles whose visible regions were selected by depth.

Design Goals

The first goal was to establish a reliable display path and then use it to demonstrate increasingly capable graphics hardware:

• Generate a standard 640×480 VGA signal.
• Rasterize fixed, two-dimensional triangles as the display scans.
• Resolve which triangle supplies the pixel colour where two triangles overlap.

These were early, bounded demonstrations—not a general-purpose GPU. The initial triangle geometry was fixed in the design; there were no 3D transforms or shading.

Why VGA?

VGA was the practical display option for this board and toolchain. The open FPGA toolchain in use could not place the differential outputs required by the HDMI/DVI path. That was a limitation of the toolchain, not a universal limitation of the FPGA or of HDMI/DVI.

For 640×480 VGA, the board’s 50 MHz clock was divided by two to produce a 25 MHz pixel clock. The initial colour-bar design used a simple three-resistor DAC, with one output bit per colour channel—enough for eight colours. That test-pattern implementation used 246 LUTs and 54 flip-flops.

The VGA pin mapping was measured rather than assumed from conflicting documentation. A beacon bitstream and logic analyser identified HSYNC at FPGA pin D5 and VSYNC at E5. Logic-analyser measurements of the display signal showed HSYNC at 31,248.25 Hz, about 0.006% from the 31,250 Hz target, consistent with 640×480 VGA timing.

Implementation: Follow the Display Beam

The renderer evaluates coverage and depth in step with the display scan. Triangle setup data supplies the edge coefficients, vertex depths, and colours. Timing signals control the incremental accumulators; coverage and depth determine which colour is sent to the display.

Board clock and reset
        │
        ▼
VGA timing ──► pixel position, sync, active-video
        │
        ├──► edge accumulators ──► triangle coverage
        │
Triangle setup data
(edges, vertex depths, colours)
        │
        ├──► depth setup ──► depth accumulators
        │                         │
        └─────────────────────────┴──► depth comparison
                                            │
                                    winning pixel colour
                                            │
                                   align colour with sync
                                            ▼
                                        VGA output

The edge accumulators determine whether the current pixel lies inside each triangle. For covered pixels, the depth path provides the per-pixel depth values; the nearer triangle wins, with ties going to triangle 0. The selected colour is aligned with the video timing and sent directly to VGA. The renderer does not store a complete frame in a framebuffer.

This diagram describes the later two-triangle depth path. The first colour-bar demonstration had no rasterizer, and the first triangle demonstration did not exercise depth selection.

The First Pixels and Display Evidence

┌───────────┬─────────────────┬────────────────────────────────────────────┐
│ Date      │ What appeared   │ What the evidence supports                 │
├───────────┼─────────────────┼────────────────────────────────────────────┤
│ 4         │ VGA colour bars │ Physical display output and logic-analyser │
│ September │ and a moving    │ timing measurements                        │
│           │ marker          │                                            │
├───────────┼─────────────────┼────────────────────────────────────────────┤
│ 5         │ One rasterized  │ Physical observation of fixed 2D geometry  │
│ September │ triangle        │                                            │
├───────────┼─────────────────┼────────────────────────────────────────────┤
│ 6         │ Two overlapping │ Physical monitor photographs; the          │
│ September │ triangles       │ corresponding design matched an            │
│           │ resolved by     │ independent full-frame oracle in           │
│           │ depth           │ simulation                                 │
└───────────┴─────────────────┴────────────────────────────────────────────┘

For the 6 September result, the simulation comparison covered all 307,200 pixels in the 640×480 frame. The physical result was assessed from monitor photographs; there was no exact pixel capture from the FPGA output.

Further Goals

Later work explored scene updates, interpolated attributes, and material patterns. Those are separate steps beyond the first display demonstrations. The early results had no 3D transforms or shading, and their triangle setup was fixed rather than supplied through a live scene interface.

The detailed measurements and evidence boundaries are recorded in the SPU hardware evidence ledger, especially §§3.8–3.10.

One small editorial choice remains: the title could be “From VGA Test Pattern to Depth-Resolved Triangles” to make the three-stage progression immediately clear.

Agreed. “My FPGA Toolchain Had Been Dead for Weeks and I Didn’t Know” should stand on its own as a first-person engineering story. Its strength is the process of separating toolchain, backend, measurement, and hardware problems that initially looked like design faults—not a list of failures.

I’d keep the programmer fault explicitly unresolved, describe HDMI as a blocker in the tested toolchain configuration, and soften “the encoder is correct” to the reference-check wording you suggested. Then the follow-up article can focus on the graphics result: from VGA test pattern to rasterized triangle and depth-resolved overlap, with each evidence boundary clear.

Together, the pieces show both how the project debugged its way forward and what the GPU work eventually demonstrated.

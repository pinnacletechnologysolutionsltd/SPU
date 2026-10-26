# Engineering Contract: Wukong GPU Prepared-Scene Atomic Activation T1b

**Date:** 2026-09-11  
**Status:** COMPLETE — B1 selected by static inspection, 2026-09-11  
**Authorization:** Owner authorized 2026-09-11  

## Objective

Identify, without implementation, the minimum boundary at which the raw
two-triangle scene, coverage inputs, and derived depth state can be made
complete and mutually consistent before atomic renderer activation.

## Scope

Static inspection of existing GPU RTL is authorized. One non-modifying
simulation probe is permitted only if inspection cannot resolve a necessary
timing question. RTL changes, T1a changes, UART integration, synthesis, P&R,
hardware, arithmetic changes, duplicated arithmetic, and optimization are
prohibited.

## Required result

Trace raw scene state through coverage setup, shared depth dispatch, derived
depth coefficients, attribute execution state, and `frame_start`. Classify the
minimum architecture as B1, B2, B3, B4, or E; document readiness predicates,
mid-preparation behavior, retained-state cost, and the exact activation
boundary. Stop after the architectural result.

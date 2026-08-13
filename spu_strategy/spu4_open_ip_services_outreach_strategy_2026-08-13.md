# SPU-4 open-IP services and outreach strategy

**Date:** 2026-08-13  
**Direction:** SPU-4 production-facing work, with SPU-13 continuing as the higher-value advanced platform

## Commercial thesis

The SPU-4 RTL and mathematical architecture remain open. The commercial offer
is the expertise and engineering around that open foundation:

- architecture selection and problem modelling;
- FPGA porting and integration;
- deterministic arithmetic and verification;
- board bring-up and reproducible build flows;
- application development;
- team training and handover.

The value is not secrecy around a small RTL block. It is the ability to turn a
customer's sensing, geometry, or deterministic-control problem into a verified
implementation that their team can understand and maintain.

SPU-13 remains the platform with the greatest technical and commercial
potential. It has a higher cost and a higher entry point, so SPU-4 is the
practical first engagement: a smaller system through which customers can learn
the architecture, prove a use case, and later expand into SPU-13 capability.

## Two-tier architecture

The product boundary should have two layers:

```text
customer system → spu4_customer_wrapper → spu4_core
                                      ↘ optional telemetry / bridge
advanced system → SPU-13 services and research platform
```

### Stable reusable core

`spu4_core` is the implementation layer: Euclidean arithmetic, sequencing,
registers, and the deterministic datapath. It should change conservatively and
remain reusable across applications and FPGA targets.

### Customer-facing wrapper

`spu4_customer_wrapper` is the contract layer around the core. It hides
development-era implementation details and defines:

- clock and reset behaviour;
- signed feature or Quadray input widths;
- `start`, `busy`, and `done` handshakes;
- coefficient and configuration loading;
- result registers;
- status and telemetry fields;
- fixed or explicitly bounded latency;
- optional streaming, SPI, or memory-mapped adapters.

The existing `hardware/rtl/core/spu4/spu4_standalone_top.v` is the starting
reference, not yet the final customer ABI. T7.4 should document and freeze the
smallest useful wrapper before adding application-specific interfaces.

The first sensor demonstrator can therefore use:

```text
INA226 → Pico/RP2040 logger → deterministic feature extraction
       → SPU-4 customer wrapper → SOM1 decision path and telemetry
```

The INA226 interface should initially remain outside the SPU-4 core. This
keeps the core useful for industrial sensing, robotics, geometry, and other
feature sources while allowing the demonstrator to exercise a real end-to-end
application.

## Product ladder

### 1. Open reference core

Publish the SPU-4 source, simulator/test material, reference Tang 25K build,
interface documentation, and claim ledger. Keep the base claim narrow:
deterministic arithmetic and bounded telemetry. Do not imply comprehensive
self-fault detection; see `docs/SPU4_FAULT_REPORTING_CONTRACT.md`.

### 2. Application demonstrator

Build one narrow Sentinel/SOM demonstration:

```text
sensor stream → deterministic feature/BMU block → anomaly/winner telemetry
             → host dashboard or SPU-13 research node
```

Condition monitoring and low-power anomaly detection are good first examples,
but the SOM edge tier remains an application package until its upload path,
board top, synthesis record, and silicon evidence are complete.

### 3. Paid engineering packages

- feasibility study and architecture selection;
- FPGA target port and resource/timing closure;
- customer-specific feature or telemetry integration;
- verification, fault injection, and reproducibility audit;
- board bring-up;
- developer training and maintenance handover.

Repeated customer work should become reusable open modules and documented
deployment packages.

## Target conversations

Start with engineers who have a concrete deterministic embedded problem:

- industrial sensing and condition monitoring;
- robotics and exact kinematics;
- small FPGA teams moving an algorithm from software to hardware;
- university FPGA/open-hardware programmes;
- open-hardware teams needing a verified arithmetic or telemetry subsystem.

Lead with the problem solved, not with the phrase “field processor.” A useful
conversation opener is:

> Bring us a sensing, geometry, or deterministic-control problem that needs to
> run on FPGA. We will model it exactly, build a reproducible reference
> implementation, and train your team to maintain it.

## Public communication

Begin outreach before the full product package is finished, but make it an
educational pilot campaign rather than a broad launch.

### Homepage

The homepage is the canonical source: product brief, claim ledger, downloads,
reference build, evidence links, and contact form. Every public claim should
link to the appropriate RTL, theorem, synthesis, or hardware evidence.

### LinkedIn

Primary channel for FPGA engineers, robotics companies, industrial developers,
consultants, and training contacts. Post concise engineering lessons,
build-to-silicon results, and invitations to discuss concrete problems.

### YouTube

Use short demonstrations rather than polished promotional videos initially:

1. What the SPU-4 Sentinel is.
2. From open RTL to verified FPGA silicon.
3. A deterministic anomaly-detection node.
4. How exact arithmetic differs from floating-point firmware.

Show the command, target, output, and scope of each demonstration. Label
expected output separately from observed hardware output.

### X

Use as a secondary technical discovery channel for open-source FPGA and
hardware audiences. Cross-post short findings and link back to the canonical
homepage article.

## Editorial rules

- Say “open architecture” and “paid implementation expertise,” not “proprietary
  IP,” unless a customer-specific deliverable is actually closed.
- Separate RTL-verified, silicon-proven, synthesis-estimated, and experimental
  claims.
- Do not market the approximate 400-LUT figure as universal; it is a
  synthesis/P&R estimate including the probe fixture.
- Do not call the base SPU-4 self-checking until a separate fault package exists.
- Use real captures for silicon demonstrations; mark simulations and expected
  transcripts clearly.
- Invite collaboration around customer problems rather than promising a
  finished universal solution.

## SPU-13 advanced platform

Continue SPU-13 work as experimental hardware, research demonstrations, grant
material, and specialist consulting capability. Its exact SOM, robotics, RPLU,
Lucas/φ arithmetic, and higher-dimensional research make it the advanced,
higher-value platform rather than a superseded project.

The SPU-13 track should not block the SPU-4 product package, but successful
SPU-4 engagements should create a route into SPU-13: a customer begins with a
small deterministic feature or telemetry problem, then expands when the
application needs richer exact arithmetic, larger maps, or advanced geometry.

## First campaign checklist

1. Publish a one-page SPU-4 product brief and wrapper/interface diagram.
2. Link the product brief to the claim and fault-reporting ledgers.
3. Record one short build/flash/telemetry demonstration.
4. Publish the same technical article on the homepage and LinkedIn.
5. Contact a small set of FPGA, sensing, robotics, and university prospects.
6. Record their concrete problems and use those conversations to select the
   first supported application package.
7. Define the path from a successful SPU-4 pilot to an SPU-13 advanced
   engagement, without requiring SPU-13 to be production-complete first.

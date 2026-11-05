#!/usr/bin/env python3
"""Check KiCad's exported candidate netlist against the reviewed pin tables."""
from pathlib import Path
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
root = ET.parse(HERE / 'netlist.xml').getroot()
nets = {
    (node.attrib['ref'], node.attrib['pin']): net.attrib['name'].removeprefix('/')
    for net in root.findall('./nets/net') for node in net.findall('node')
}
P, F, G = 'PICO_3V3', 'TARGET_VCCO_3V3', 'GND'
expected = {
    'U1': [P, 'P_SCK', 'P_CS_N', G, P, 'CS_DRV', 'SCK_DRV', F],
    'U2': [P, G, 'P_MOSI', 'MOSI_DRV', P, F],
    'U3': [P, G, 'MISO_DRV', 'F_MISO', G, F],
    'J2': ['F_CS_N', 'F_MOSI', 'F_MISO', 'F_SCK', G, F],
    'R1': ['SCK_DRV', 'F_SCK'], 'R2': ['CS_DRV', 'F_CS_N'],
    'R3': ['MOSI_DRV', 'F_MOSI'], 'R4': ['MISO_DRV', 'P_MISO'],
    'R5': [P, 'P_CS_N'], 'R6': [G, 'P_SCK'],
    'R7': [G, 'P_MOSI'], 'R8': [G, 'P_MISO'],
    'R9': [F, 'F_CS_N'], 'R10': [G, 'F_SCK'],
    'R11': [G, 'F_MOSI'], 'R12': [G, 'F_MISO'],
    **{f'C{i}': [P if i % 2 else F, G] for i in range(1, 7)},
}
checks = {(ref, str(pin)): net for ref, pins in expected.items()
          for pin, net in enumerate(pins, 1)}
checks.update({('A1', str(pin)): net for pin, net in {
    21: 'P_MISO', 22: 'P_CS_N', 24: 'P_SCK', 25: 'P_MOSI', 36: P,
    **{pin: G for pin in (3, 8, 13, 18, 23, 28, 38)},
}.items()})
errors = [f'{ref}.{pin}: expected {net}, got {nets.get((ref, pin))}'
          for (ref, pin), net in checks.items() if nets.get((ref, pin)) != net]
components = {c.attrib['ref']: c for c in root.findall('./components/comp')}
if set(components) != {'A1', *expected}:
    errors.append('Unexpected component inventory')
for ref in components:
    c = components[ref]
    if ref.startswith('R'):
        want = '100' if int(ref[1:]) <= 4 else '10k'
        if c.findtext('value') != want:
            errors.append(f'{ref}: wrong resistance')
    if ref.startswith('C') and c.findtext('value') != '100n 16V X7R':
        errors.append(f'{ref}: wrong bypass value')
for ref, mpn, footprint in [
    ('U1', 'SN74LVC2T45DCUR', 'Package_SO:VSSOP-8_2.3x2mm_P0.5mm'),
    ('U2', 'SN74LVC1T45DBVR', 'Package_TO_SOT_SMD:SOT-23-6'),
    ('U3', 'SN74LVC1T45DBVR', 'Package_TO_SOT_SMD:SOT-23-6'),
    ('A1', 'SC1631', 'Module:RaspberryPi_Pico_Common_THT'),
]:
    c = components[ref]
    if c.findtext("fields/field[@name='MPN']") != mpn:
        errors.append(f'{ref}: wrong manufacturer part')
    if c.findtext('footprint') != footprint:
        errors.append(f'{ref}: wrong footprint')
if errors:
    raise SystemExit('\n'.join(errors))
print(f'PASS: {len(checks)} connected pins; {len(components)} components; '
      'resistor/capacitor values; module/translator identities and footprints')
print('Netlist consistency only; no electrical qualification.')

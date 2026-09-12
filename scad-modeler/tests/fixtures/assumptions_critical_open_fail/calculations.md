# Calculations

Reproduction of a real project's table (steering_reduction_gearbox, 2026-09-12),
reduced to the rows that matter. Both entries below are 'Critical' and still
'Open', which is exactly why `check_assumptions.py` exists: a load-bearing
number that nobody verified reads the same as one that was.

| ID | Type | Criticality | Statement | Status | Evidence |
|---|---|---|---|---|---|
| D1 | Assumption | Critical | Worm efficiency eta ~ 0.5 -- UNMEASURED; the whole torque budget rests on it | Open | none |
| D2 | Risk | Critical | Motor RPM/CPR unknown (3000-10000 band); the entire 80:1 ratio choice depends on it | Open | none |
| D3 | Assumption | Ordinary | Panel reveal is cosmetic only | Open | n/a |

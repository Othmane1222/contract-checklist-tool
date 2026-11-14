# Evaluation report

| | |
|---|---|
| Date | 2026-11-14 16:33 UTC |
| Commit | 94823ea-dirty |
| Model | deepseek-flash (temperature 0, thinking disabled) |
| Split | dev: 2 contracts × 2 runs |
| Held-out runs so far | 0 |
| Failed runs | 0 of 4 |

## Overall

| Metric | Result | Coverage |
|---|---|---|
| Found accuracy | 83% | 100% decided automatically (12 of 12) |
| False "missing" | 0 | |
| False "present" | 2 | |
| Sent to manual check | 0 unverified, 0 possibly present | |
| Risk: exact match | 80% | 10 of 10 present items scored |
| Risk: within one level | 100% | 10 of 10 present items scored |
| High rated as Low | 0 | |
| Quote inside labelled article | 100% | 10 checked, 0 could not be placed |
| Consistency across runs | 100% | 6 item results compared |

## Per item

| Item | Found accuracy | Coverage | False missing | False present | Manual check | Risk exact (scored) | Risk within one | High as Low |
|---|---|---|---|---|---|---|---|---|
| employment/contract_term | 100% | 100% | 0 | 0 | 0 | 100% (2) | 100% | 0 |
| employment/probation | 100% | 100% | 0 | 0 | 0 | 100% (2) | 100% | 0 |
| employment/termination | 0% | 100% | 0 | 2 | 0 | — (0) | — | 0 |
| lease/early_termination | 100% | 100% | 0 | 0 | 0 | 100% (2) | 100% | 0 |
| lease/rent_deposit | 100% | 100% | 0 | 0 | 0 | 0% (2) | 100% | 0 |
| lease/repairs | 100% | 100% | 0 | 0 | 0 | 100% (2) | 100% | 0 |

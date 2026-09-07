# SmallChip AI 100M scaling — measured numbers

Source: `/Users/harshith/Documents/ChipPlacer/results/scaling_100m_v3.json`

| Scale | Cells | Nets | Blocks | Worker time (s) | Per-net HPWL (DBU) |
|---|---|---|---|---|---|
| 15K_baseline | 15,000 | 13,155 | 3 | 9.4 | 7,008 |
| 150K | 150,000 | 131,570 | 10 | 0.4 | 73,548 |
| 1M | 1,005,000 | 881,519 | 67 | 4.2 | 220,522 |
| 5M | 4,995,000 | 4,381,281 | 333 | 6.8 | 513,218 |
| 10M | 10,005,000 | 8,775,719 | 667 | 32894.5 | 734,298 |

## References

- DREAMPlace (adaptec1, 211K cells): ~32M HPWL total = ~152,000 DBU/net, 30 min on V100 GPU
- RePlAce (adaptec1): 16.19M HPWL = ~34,700 DBU/net
- SmallChip AI per-block: random for ≥150K (V3 too slow at 15K+ blocks), V3 for 15K baseline
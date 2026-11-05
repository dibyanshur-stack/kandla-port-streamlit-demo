# Included real acquisition dates

Selected tuned RF-2 `rf2_002`; compressed real scene previews only. Statistics describe full-resolution unique source pixels, with overlapping windows deduplicated. No pixel annotation layers are public.

| Date | Scene ID | Preview (height × width) | Unique valid pixels | Ship pixels |
|---|---|---|---:|---:|
| 20260531 | `20260531_063100_24_2504_3B` | 1024 × 293 | 1,492,826 | 79,447 |
| 20260603 | `20260603_063613_80_250a_3B` | 1024 × 293 | 1,485,490 | 87,940 |
| 20260604 | `20260604_062718_84_251e_3B` | 1024 × 293 | 1,472,092 | 58,435 |

Immutable validation inventory: 5 scenes on 5 dates.

## Dates not exported

- 20260523 — `20260523_063320_34_2540_3B`: Source available; selected RF-2 scene inference pending (run exporter without --cached-only)
- 20260524 — `20260524_062750_42_2538_3B`: Source available; selected RF-2 scene inference pending (run exporter without --cached-only)

Source CRS/affine, preview sampling, coverage, overlap observations and model fingerprints remain in scene JSON. Separate scene footprints are never pooled into date-level unique areas.

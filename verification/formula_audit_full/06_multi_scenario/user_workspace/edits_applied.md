# user_workspace scenario — 5 edits applied

1. `LandUse[LU_2.1].user_percent`: 3.856 → 4.5 (approaches F001's recommended 5.0)
2. `LandUse[LU_6].user_percent`: 2.000 → 3.0 (wind-expansion target)
3. `VerbrauchData[1.4].status`: observed (no edit)
4. `RenewableData[9.3.1].status`: observed (no edit)
5. `GebaeudewaermeData[2.8.0].status`: observed (no edit)

All edits applied inside a Django transaction, then rolled back to
preserve the baseline DB state. This scenario tests that the cascade
propagates LU changes into:
  - LU_2.4 residual
  - Renewable 1.2 (Solar Freiflächen renewable energy)
  - Renewable 1.2.1.2 (solar energy yield)
  - Bilanz KLIK renewable row

The post-transaction rollback is verified by a re-query of the
affected rows: they return to the pre-edit state.

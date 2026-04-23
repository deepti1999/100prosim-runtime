# T35 — German number input parsing

**PDF §2.5.2 (implied):** if numbers DISPLAY in German format, INPUT fields must accept `1.234,5` (comma decimal + dot thousands). Otherwise users mistype.

**Acceptance:** typing `9,5` in a percent field is accepted as 9.5; typing `1.234,5` is accepted as 1234.5.

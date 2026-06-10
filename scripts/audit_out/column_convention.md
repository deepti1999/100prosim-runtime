# D.xlsx column convention (value-match derived)

For each model, which column of D.xlsx supplied a value matching our DB `status` / `ziel` fields. Higher count = more reliable convention.

## landuse (n=20)

- confidence: `{'MED-VALUE-ONLY': 4, 'LOW': 16}`
- status sourced from: `{'W': 4}`
- ziel sourced from:   `{'W': 4}`

## renewabledata (n=223)

- confidence: `{'LOW': 178, 'MED-VALUE-ONLY': 45}`
- status sourced from: `{'AG': 8, 'W': 35, 'AN': 1, 'U': 1}`
- ziel sourced from:   `{'AG': 8, 'W': 34, 'AN': 2, 'U': 1}`

## verbrauchdata (n=151)

- confidence: `{'LOW': 108, 'MED-VALUE-ONLY': 43}`
- status sourced from: `{'W': 30, 'AN': 7, 'AG': 4, 'U': 2}`
- ziel sourced from:   `{'W': 32, 'AN': 7, 'AG': 4}`

## gebaeudewaermedata (n=26)

- confidence: `{'MED-VALUE-ONLY': 10, 'LOW': 15, 'MED': 1}`
- status sourced from: `{'W': 9, 'U': 2}`
- ziel sourced from:   `{'W': 10}`


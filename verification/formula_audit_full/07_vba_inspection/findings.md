# §07 VBA Inspection — findings

Total pattern hits across all files: 34


## _100prosim.xlsm


### on_open — 1 hits

- `DieseArbeitsmappe.cls` line 9: `Private Sub Workbook_Open()`

## AH.xlsm


### cell_mutator — 22 hits

- `Modul1.bas` line 48: `Range("Archiviert").Value = 0`
- `Modul1.bas` line 90: `Range("Archiviert").Value = 0`
- `Modul1.bas` line 204: `Range("Archiviert").Value = 2   'Unterscheidung zu 1 am Ende des normalen Durchlaufs`
- `Modul1.bas` line 207: `If Range("CP2SzenKenn").Value = "" Then`
- `Modul1.bas` line 209: `Range("Archiviert").Value = 2   'Unterscheidung zu 1 am Ende des normalen Durchlaufs`
- `Modul1.bas` line 215: `Range("MonSzenKenn").Value = SzenStandKenn`
- `Modul1.bas` line 224: `Range("Archiviert").Value = 1`
- `Modul1.bas` line 310: `Range("AE5").Value = 0`
- `Modul1.bas` line 318: `Range("AL6").Value = "Basis"`
- `Modul4.bas` line 42: `'    Range("Archiviert").Value = 0`
- `Modul4.bas` line 66: `'    Range("Archiviert").Value = 0`
- `Modul4.bas` line 102: `'    Range("AL1").Value = Datum1`
- `Modul4.bas` line 104: `'    Range("AM1").Value = Zeit1`
- `Modul4.bas` line 187: `'        Range("Archiviert").Value = 2   'Unterscheidung zu 1 am Ende des normalen Durchlaufs`
- `Modul4.bas` line 190: `'    If Range("CP2SzenKenn").Value = "" Then`
- `Modul4.bas` line 192: `'        Range("Archiviert").Value = 2   'Unterscheidung zu 1 am Ende des normalen Durchlaufs`
- `Modul4.bas` line 198: `'    Range("MonSzenKenn").Value = SzenStandKenn`
- `Modul4.bas` line 207: `'    Range("Archiviert").Value = 1`
- `Modul4.bas` line 293: `'        Range("AE5").Value = 0`
- `Modul4.bas` line 301: `'        Range("AL6").Value = "Basis"`

(+ 2 more)

### calc_trigger — 4 hits

- `Step2.bas` line 35: `Application.Calculate`
- `Step2.bas` line 60: `Application.Calculate`
- `s_mod_m237.bas` line 30: `Application.Calculate`
- `s_mod_m237.bas` line 38: `Application.Calculate`

### password_protect — 5 hits

- `Modul1.bas` line 218: `Sheets("Monitor").Protect Password:="m"`
- `Modul1.bas` line 339: `Sheets("Monitor").Protect Password:="m"`
- `Modul4.bas` line 201: `'    Sheets("Monitor").Protect Password:="m"`
- `Modul4.bas` line 322: `'        Sheets("Monitor").Protect Password:="m"`
- `Modul2.bas` line 47: `Sheets("Monitor").Protect Password:="m"`

## WS.xlsm


### cell_mutator — 2 hits

- `Tabelle10.cls` line 24: `' Range("AL1").Value = Datum1`
- `Tabelle10.cls` line 26: `' Range("AM1").Value = Zeit1`

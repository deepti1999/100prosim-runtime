# 100prosim-Web — Bestandsaufnahme

**Autor:** H. Schmidt-Kanefendt (ErnES)
**Datum:** 03.04.2026
**Quell-PDF:** `260403_Portierung_Bestandsaufnahme.pdf` (12 Seiten)

> Wortlaut-Extraktion des Stakeholder-Dokuments. Inhaltlich unverändert; nur Layout zu Markdown konvertiert.

---

## 1 Anlass

Die Entwicklungsarbeit von Deepti Maheedharan zur Portierung von 100prosim zu einem webfähigen Tool im Rahmen ihres Masterstudiums ist zum März 2026 abgeschlossen. Sie hat mit der fehlerfreien Realisierung der kompletten Kernfunktionalität einen wesentlich höheren Entwicklungsstand erreicht, als bei der komplexen Aufgabe zu erwarten war – **eine großartige Leistung!**

Das **Interesse von ErnES** liegt nun darin, das Tool zur Einsatzreife zu bringen und darüber hinaus möglichst einen Stand zu erreichen, mit dem das Excel-100prosim mit seinem gesamten relevanten Leistungsspektrum abgelöst werden kann. Als Basis für die **Weiterentwicklung** des erreichten Standes soll die folgende Bestandsaufnahme dienen: Was fehlt noch an der **Einsatzreife / Ablösereife**?

---

## 2 Bestandsaufnahme

### 2.1 Hosting

Deepti hatte inzwischen das Hosting des Tools beendet. Auf Nachfragen von Ute und mir hat sie zur Fortführung der Testphase das Hosting am 27.03.2026 neu eingerichtet unter der Adresse <https://prosim-web-20260327121034-61780921a6b9.herokuapp.com/renewable/>. Die Login-Userdaten aus dem vorhergehenden Hosting waren nicht mehr bekannt und mussten neu eingerichtet werden.

Die Übernahme der 100prosim-Webanwendung durch ErnES setzt die Installation auf einer eigenen Rechnerplattform voraus. Für einen glatten Übergang **erforderlich** ist **bis zum Ende der Testphase**:

- die **Bereitstellung** einer geeigneten **Rechnerplattform**
- **lauffähige Installation**
- die Bildung von **Hosting-Knowhow** bei **ErnES-AdministratorInnen** (mindestens 2 Personen, um Ausfall-Situationen zu vermeiden).

### 2.2 Antwortzeiten

**Testfall:** Im Basis-Szenario wird die Onshore-Windparkfläche von 2,0 % auf 2,3 % erhöht und die Offshore-Leistung von 70 GW auf 60 GW vermindert. Der Abgleich dauert in 100prosim-Excel **5,8 Sekunden**, in 100prosim-Web **120 Sekunden**, also die **20-fache Antwortzeit**.

**Praxistaugliche Antwortzeiten** sind **Grundvoraussetzung** für die **Einsatzfähigkeit**. Nach der Installation auf einer leistungsfähigen Rechnerplattform ist deshalb **als erstes** die damit erreichbare Antwortzeit zu **testen**. Je größer sich die Leistungssteigerung der Rechnerplattform im Vergleich zu dem bisher von Deepti als Host verwendeten PC erweist, desto eher werden die Nachteile der verwendeten Softwarelösung aufgefangen. Dieser Test wird damit zur **Nagelprobe** für die Einsatzfähigkeit von 100prosim-Web im aktuellen Stand.

Falls so keine praxistauglichen Antwortzeiten erreicht werden, müsste die Software-Architektur überprüft und überarbeitet werden.

### 2.3 Datenmodell

**Vorschlag:** Schnittstelle zur Nutzung der bestehenden Excel-Datenmodell-Dateien anstelle des integrierten Datenmodells im aktuellen 100prosim-Web (Begründung im Folgenden).

#### 2.3.1 Nachvollziehbarkeit

In 100prosim-Excel sind für jeden Parameter-Ansatz die Quellbezüge und getroffenen Annahmen einfach und direkt über Verlinkung nachvollziehbar. Das ist der entscheidende Unterschied zu einer Spielkonsole.

Im aktuellen 100prosim-Web sind Herkunft und Belastbarkeit der Parameter-Ansätze nicht nachvollziehbar. Dies ist aber **Grundvoraussetzung** für den **Erkenntnisgewinn** der Anwendenden durch kritische **Auseinandersetzung** zur Erweiterung und **Festigung** der **eigenen Einschätzung**. Dies gilt auch für die Parameter-**Aktualisierung** des **Basis-Szenarios** durch die Administrierenden, die zum Erhalt der Einsatztauglichkeit von Zeit zu Zeit erforderlich ist.

#### 2.3.2 Alternativ-Regionen

Mit 100prosim-Excel wurde nicht nur die Region Deutschland als Basis-Szenario abgebildet, sondern auch verschiedene Bundesländer (<https://www.ernes.de/seite/422657/softwaretools.html>). Damit lassen sich die spezifischen Gegebenheiten der Region berücksichtigen. Ermöglicht wird dies durch die modulare Architektur, in der allein das Datenmodell sämtliche Regions-Spezifika enthält und so einfach austauschbar ist. Das Editieren des Datenmodells erfolgt hier in einer Excel-Datei (`D.xlsx`), spezielle Admin-Rechte sind nicht erforderlich.

Das aktuelle 100prosim-Web ist auf ein Deutschland-Datenmodell beschränkt. Erstellung und Zugriff auf Datenmodelle verschiedener Alternativ-Regionen wird nicht unterstützt. Dadurch ist eine regionsspezifische Anwendung, wie sie z. B. von verschiedenen Grünen-Landesarbeitsgemeinschaften intensiv genutzt wurde, nicht verfügbar.

**Vorschlag: Schnittstelle** zur Nutzung der **bestehenden Excel-Datenmodell-Dateien** anstelle des integrierten Datenmodells im aktuellen 100prosim-Web.

### 2.4 Cockpit-Funktionalität

#### 2.4.1 Basis-Wert Verfügbarkeit

In 100prosim-Excel bleibt nach Modifikation eines Zielparameters (roter Pfeil) der ursprüngliche Wert im Datenmodell des Basis-Szenarios unverändert erhalten. Nach Löschen der Modifikation erscheint automatisch wieder der ursprüngliche Wert aus dem Datenmodell in dem in Arbeit befindlichen Szenario (grüner Pfeil).

Diese **Verfügbarkeit des Basis-Wertes erlaubt** die einfache Rücknahme einer als nicht sinnvoll erkannten Modifikation und damit das **freie Experimentieren** auf einer **bleibenden Grundlage**.

Beim aktuellen 100prosim-Web ist der Basis-Wert nach Modifikation nicht mehr verfügbar. Nach Löschen des Modifikations-Wertes im Modifikations-Feld erscheint dort nach wie vor der zuletzt eingegebene Wert. Das erschwert die Übersicht, insbesondere bei einer komplexen Modifikation mehrerer Parameter.

#### 2.4.2 Baseline

Im aktuellen 100prosim-Web wird angeboten, über den Button „Baseline" (obere Menüleiste 3. von rechts) „Baseline erstellen" den aktuellen Stand als Basiszenario zu speichern, um nach Abschluss einer Szenario-Modifikation über „Auf Baseline zurücksetzen" wieder diesen Basisszenario-Stand für eine neue Modifikation zu laden. Dies funktioniert aber nur, wenn ein vorhergehender Szenario-Stand als Baseline gespeichert worden war (mit „Baseline" in der oberen Menüzeile rechts, und dann „Baseline erstellen"). **Nachteile:**

1. Eine **versäumte Baseline-Erstellung** ist **nicht** mehr **nachholbar**, es steht dann keine Baseline zur Verfügung.
2. Im Unterschied zu 100prosim-Excel ist es so nicht möglich, den Anwendenden ein zentrales Basisszenario als gemeinsame Baseline vorzulegen, wodurch **Beurteilung und Vergleich verschiedener Modifikationen** sehr **erschwert** würde.

**Vorschlag:** Menüpunkt „Baseline" – „Auf Baseline zurücksetzen" dazu nutzen, als Baseline das administrierte Basisszenario zu laden (siehe auch 2.4.1 und 2.4.2), der Menüpunkt „Baseline erstellen" kann entfallen.

#### 2.4.3 Szenario-Abgleich

In 100prosim-Excel werden für den Szenario-Bilanzabgleich zwischen Verbrauch und Erzeugung genau **zwei Optionen** angeboten: Die Anpassung der Solarfreiflächen oder die Anpassung der Onshore-Windparkflächen.

Beim aktuellen 100prosim-Web existieren dagegen **6 Buttons:**

- Goal Seek ausführen
- WS Balance Solar
- Sector + WS Solar Balance
- WS Balance Wind
- Sector + WS Wind Balance
- Aktualisieren

Auch bei ausführlicher Erläuterung der unterschiedlichen damit ausgelösten Aktionen im Benutzerhandbuch würden die Anwendenden stark gefordert mit dem Erwerb von Sicherheit bei der Auswahl des jeweils passenden Buttons.

Wenn ich es richtig interpretiere, sind die Buttons **„Goal Seek"** und **„Aktualisieren"** überflüssig, da die Funktionen ohnehin beim Öffnen des Fensters „Szenario-Abgleich" und nach „Balance" automatisch ablaufen. Falls das zutrifft, wären sie zu **löschen**.

Unklar ist, weshalb die Buttons **„WS Balance …"** und **„Sector + WS … Balance"** jeweils **nacheinander** in dieser Reihenfolge **betätigt** werden müssen. Dies sollte durch jeweils **einen Button** WS Balance Wind bzw. WS Balance Solar möglich gemacht werden. Während der Tests waren die Buttons nach Szenario-Änderungen meist ohne Funktion, nach Betätigung erfolgte kein Abgleich und keine Busy-Anzeige.

#### 2.4.4 Recalculate

Beim aktuellen 100prosim-Web werden die Anwendenden auf der Seite Verbrauch aufgefordert, nach jeder User-Änderung des Zielwertes auf Seite Erneuerbare zu wechseln und dort Recalculate Renewables auszuführen. Bei User Input-Änderungen auf der Seite Erneuerbare fehlt der ausdrückliche Hinweis zur Notwendigkeit von Recalculate Renewables. Unklar sind die Folgen, wenn dieser Button nach Änderungen nicht betätigt wird.

Bei 100prosim-Excel erfolgt die **gesamte Kalkulation** von Flächen, Erneuerbaren oder Verbrauch nach **jeder Änderung sofort automatisch**. Von den Anwendenden ist so keine Aufmerksamkeit erforderlich und Fehlinterpretationen durch versehentlich unterlassene Kalkulation werden vermieden.

#### 2.4.5 Save All Values

Beim aktuellen 100prosim-Web wird den Anwendenden auf der Seite „Flächen" der Button „Save All Values" angeboten. Die Speicherung der Flächenwerte soll vermutlich eine spätere Wiederherstellung des gespeicherten Flächendaten-Standes ermöglichen. Allerdings ist dies weder für die User-Daten der Erneuerbaren noch für den Verbrauch vorgesehen. Die Funktion wäre nur dann sinnvoll, wenn sämtliche Scenario-Werte für eine spätere Weiterbearbeitung dieser Szenariovariante gespeichert würden. Dies wird offenbar durch „Scenarios" – „Save current Scenario" (obere Menüleiste rechts) ermöglicht. Wenn dem so ist, ist der **Button „Save All Values" überflüssig** und unnötig verwirrend.

### 2.5 Cockpit-Layout

#### 2.5.1 Englisch - Deutsch

Im aktuellen 100prosim-Web sind ein erheblicher Teil der Begriffe noch nicht vom Englischen ins Deutsche übertragen. Beispiel: Zwar heißt es in den **Menüleisten** bereits „Erneuerbare Energien", die Überschrift der Seite lautet aber noch „Renewable Energy…". Auch sämtliche **Spalten** und **Buttons** sind noch **englisch** beschriftet. Die Uneinheitlichkeit stellt die Anwendenden vor unnötige Anforderungen und ist eine Quelle für Fehlinterpretationen.

Auch das **Benutzerhandbuch** ist zurzeit **komplett** in **englischer** Sprache, was das **Verständnis** der teilweise schon deutschen Menü-Funktionen **erschwert**. Bei der Nutzung einer Google-Übersetzung der Seite kommt es zu fehlerhafter Übersetzung von einzelnen Begriffen und Button-Bezeichnungen.

#### 2.5.2 Zahlenformat

Im aktuellen 100prosim-Web werden die Zahlenwerte im **englischen Zahlenformat** dargestellt (Komma für Tausender-Gruppierung, Punkt als Dezimaltrennzeichen). Für Anwendende aus dem deutschen Sprachraum kann das sehr **verwirrend** sein, da sie genau die umgekehrte Trennzeichenverwendung gewohnt sind (Punkt für Tausender-Gruppierung, Komma als Dezimaltrennzeichen).

Die Seite „Szenario-Abgleich" ist als einzige bereits auf deutsches Zahlenformat umgestellt.

#### 2.5.3 Menüführung

In 100prosim-Web ist die Seiten-Menüleiste links auf nahezu allen Seiten identisch vorhanden, es fehlt auf den Seiten „Verbrauch", „Jahresstrom" und „Benutzerhandbuch". Auf der Seite „Cockpit" ist es zwar vorhanden, aber anders formatiert.

Die linken Einträge in der oberen Menüleiste wären doppelt und damit überflüssig, wenn die Seiten-Menüleiste auf allen Seiten vorhanden wäre und dort auch der Menüpunkt „100prosim" angeordnet würde.

#### 2.5.4 Ergebnisübersicht

Anzeige in 100prosim-Web, wahlweise Status oder Ziel. Anzeige in 100prosim-Excel: Status und Ziel mit den einzelnen Anteilen gegenübergestellt.

**Vorschlag:** Erhöhung der Aussagekraft durch komplexes Diagramm nach Muster 100prosim-Excel.

#### 2.5.5 Modifikationsdetails

In 100prosim-Web bisher überhaupt nicht abgebildet sind Diagramme zu den Veränderungen einzelner Verbrauchs-Parameter und der daraus resultierenden Erfordernis für Energieerzeugung aus den verschiedenen Quellen. **Ohne grafische Visualisierung** nur aufgrund von Zahlen lassen sich die Eigenheiten der **komplexen Energieszenarien nicht** annähernd so umfassend **überblicken**.

Im PDF sind als Beispiel einige Visualisierungs-Ausschnitte aus 100prosim-Excel (AH Cockpit2) abgebildet: Nachfrage-Einflüsse auf Endenergieverbrauch (Variantenvergleich), Effizienz-Einflüsse, Endenergie-Verbrauch nach Anwendungsbereichen inkl. Grundstoffe, Primärenergie-Beiträge nach Quellen, Ausbau der Erneuerbaren Energiequellen.

#### 2.5.6 Flussdiagramm Strom/H2

Im aktuellen Stand von 100prosim-Web werden die Energieflüsse von Strom und Wasserstoff im Zielszenario auf der Seite „Jahresstrom" dargestellt.

Auch nach einer ersten Überarbeitung bildet die Grafik die dem Szenario zugrundeliegenden **Strukturen** noch **nicht korrekt** ab, teilweise sind die **Werte falsch zugeordnet** und wegen der **kleinen Schriftart** ist das Diagramm schlecht lesbar. Als Vorlage dient das entsprechende Diagramm aus 100prosim-Excel (siehe PDF Seite 10).

#### 2.5.7 Jahresgang Strom

Im aktuellen 100prosim-Web wird auf der Seite Bilanz der tägliche Ladezustand der Stromspeicherung durch Wasserstoff im Jahresverlauf dargestellt. Durch den Szenario-Abgleich zum Abschluss einer Modifikation wird die Erzeugung von Solar- oder Windstrom so angepasst, dass der Ladezustand am Jahresende genau dem zu Jahresanfang entspricht.

Allerdings ist aus dem Diagramm die mindestens erforderliche **Kapazität der Wasserstoffspeicherung nicht direkt ersichtlich**, da der Stand zum Jahresanfang willkürlich den Nullpunkt bildet anstatt der niedrigste Ladezustand (hier Min: -127 422 GWh). Die Mindestkapazität resultiert aus der Summe von Max – Min. Außerdem sind die **Tagesdifferenzen** zwischen Verbrauch und Wind-/Solarstromerzeugung **nicht ersichtlich**, die zur Entladung bzw. Ladung führen.

In 100prosim-Excel dagegen werden die Tageswerte der Deckungsbeiträge bzw. Überschüsse von Wind-/Solarstrom und Mangelausgleich und der daraus resultierende Speicherladezustand absolut anschaulich visualisiert.

Anstelle von Absolutwerten in GWh wird hier die Einheit **Tagesladung** verwendet, das ermöglicht die Verwendung der Skalierung unabhängig davon, ob es sich um ein Deutschland- oder ein Regionalszenario handelt (vgl. Kapitel 2.3.2).

**Vorschlag: Nachbildung** des **100prosim-Excel-Layout**.

#### 2.5.8 Modifikations-Historie

In 100prosim-Excel lässt sich die Modifikation des Basis-Szenarios Schritt für Schritt protokollieren. Im PDF ist beispielhaft ein Ausschnitt aus einem Suffizienz-Szenario gezeigt, in dem die heutige Nachfrage nach mit Energieverbrauch verbundenen Leistungen jeweils um 10 % gegenüber dem Statusjahr reduziert und der verringerte Verbrauch durch Reduzierung der Solarfreiflächen ausgeglichen wurde (Modifikationsschritte von rechts (1) nach links (8)).

Diese Funktion unterstützt den Erkenntnisgewinn, indem sie die Nachverfolgung auch komplexer Modifikationen jeweils bezüglich Maßnahme und der damit verbundenen Wirkung ermöglicht.

Im aktuellen 100prosim-Web **fehlt eine Historien-Funktion**.

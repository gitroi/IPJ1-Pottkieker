# IPJ1 - Team Pottkieker

Github Repository für eine Simulationssoftware zur Analyse des EE-Ausbaus in Deutschland bis 2030/2045

## Dateistruktur

**Wenn an dem Projekt gearbeitet wird bitte wie folgt vorgehen:**

<ins>Initial:</ins>
1. In VS-Code auf die "Welcome"-Page (erreichbar durch Strg + Shift + P -> "welcome" eingeben)
2. "Clone Git Repository" -> URL dieses Repositories einfügen und lokalen Speicherort wählen

<ins>Arbeiten (sicher):</ins>
1. Branch erstellen
    * In der Activity Bar zur "Source Control" navigieren und auf die drei Punkte beim aktuellen Repository klicken
    * Branch -> Create Branch -> sinnvollen Namen geben
2. Coden, alle Änderungen werden dabei beim committen vorerst nur in der Branch gespeichert
    * Committen: Lokal gespeicherte Änderungen werden auf Git gepusht
    * In der Source Control eine aussagekräftige Message schreiben
    * Dropdown-Menü: "Commit & Sync"
3. Wenn der Code bugfrei ist kann er auf die main-Branch gemerged werden
    * Source Control 3. Symbol von rechts (Create Pull Request)
    * Titel und Beschreibung ergänzen -> Create
    * Die Pull Request kann von allen Mitarbeitern kommentiert werden
    * Collaborators können die Request zulassen, entweder auf Github oder unten in der Activity Bar "Create Merge Commit"

<ins>Arbeiten ("unsicher"):</ins>
    Einfach im main-Branch arbeiten und darin "Commit & Sync" 


**Das Repository ist wie folgt aufgebaut:**

### Code

Hier liegen alle Python-/Jupyter-Quelldateien.

### Daten

Hier liegen alle Daten die zur Auswertung eingelesen werden wie CSV-Dateien.

### Quellen

Hier liegen Quellen, die bei der Erstellung der Software genutzt wurden.

### Sonstiges

Hier liegen alle Dateien die nicht den anderen Kategorien zugeordnet werden können (Bei Bedarf einen neuen Ordner erstellen, falls sinnvoll)

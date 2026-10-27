# Git Commands Overzicht (met voorbeelden, uitleg en aandachtspunten)

**ctrl + shift + V (preview doc)**

Deze lijst is bedoeld als snelle referentie. Pas remote-namen, branches en paden aan aan jullie repo.

**Overzichtstabel (alle commands in dit document)**

| Command                           | Korte betekenis                         |
| --------------------------------- | --------------------------------------- |
| `git init`                        | Nieuwe lokale repo starten              |
| `git clone`                       | Repo kopiëren vanaf remote              |
| `git config`                      | Git gebruiker instellen                 |
| `git status`                      | Huidige status bekijken                 |
| `git log`                         | Commitgeschiedenis bekijken             |
| `git show`                        | Details van een commit tonen            |
| `git blame`                       | Laatste bewerker per regel              |
| `git add`                         | Wijzigingen stagen                      |
| `git commit`                      | Gestage snapshot opslaan                |
| `git commit --amend`              | Laatste commit aanpassen                |
| `git diff`                        | Verschillen bekijken                    |
| `git diff main..feature/charging` | Branch-verschillen vergelijken          |
| `git branch`                      | Branches tonen                          |
| `git switch`                      | Van branch wisselen                     |
| `git checkout -b`                 | Nieuwe branch maken en wisselen         |
| `git merge`                       | Branches samenvoegen                    |
| `git rebase`                      | Commits herschikken                     |
| `git remote -v`                   | Remotes tonen                           |
| `git remote add`                  | Remote toevoegen                        |
| `git fetch`                       | Updates ophalen zonder merge            |
| `git pull`                        | Updates ophalen en mergen               |
| `git push`                        | Commits naar remote sturen              |
| `git restore`                     | Bestanden terugzetten                   |
| `git reset --soft`                | HEAD terugzetten, staging bewaren       |
| `git reset --mixed`               | HEAD terugzetten, staging leeg          |
| `git revert`                      | Commit ongedaan maken via nieuwe commit |
| `git stash`                       | Wijzigingen tijdelijk wegzetten         |
| `git stash list`                  | Stash overzicht                         |
| `git stash pop`                   | Stash terugzetten                       |
| `git mv`                          | Bestand verplaatsen/hernoemen           |
| `git rm`                          | Bestand verwijderen en stagen           |
| `git rm --cached`                 | Verwijderen uit git, lokaal houden      |
| `git tag`                         | Release/tag aanmaken                    |
| `git push origin v1.0.0`          | Tag naar remote pushen                  |
| `.gitignore`                      | Bestanden uitsluiten van tracking       |

**Starten**

1. `git init`
   Wat doet het: maakt van een map een nieuwe lokale git-repo.
   Let op: je kunt dit beter niet doen in een map die al een repo is.
   Voorbeeld:

   ```bash
   git init
   ```

2. `git clone`
   Wat doet het: kopieert een bestaande repo inclusief `.git` historie.
   Let op: draait een nieuwe map aan; doe dit niet in een bestaande projectmap.
   Voorbeeld:

   ```bash
   git clone https://github.com/org/repo.git
   ```

3. `git config`
   Wat doet het: stelt je gebruikersnaam en e-mail in voor commits.
   Let op: gebruik je school/werk‑mail als dat vereist is.
   Voorbeeld:
   ```bash
   git config --global user.name "Voornaam Achternaam"
   git config --global user.email "naam@example.com"
   ```

**Status & Geschiedenis**

1. `git status`
   Wat doet het: toont gewijzigde, gestage en niet‑gevolgde bestanden.
   Let op: check dit altijd vóór `commit` en `push`.
   Voorbeeld:

   ```bash
   git status
   ```

2. `git log`
   Wat doet het: toont commit‑geschiedenis.
   Let op: gebruik `--oneline` om snel overzicht te houden.
   Voorbeeld:

   ```bash
   git log --oneline --graph --decorate
   ```

3. `git show`
   Wat doet het: toont details van een commit (wijzigingen + metadata).
   Let op: zonder argument is dit `HEAD` (laatste commit).
   Voorbeeld:

   ```bash
   git show HEAD
   ```

4. `git blame`
   Wat doet het: toont per regel wie het laatst wijzigde.
   Let op: handig voor context, niet als “schuldvraag”.
   Voorbeeld:
   ```bash
   git blame src/backend_logic/backend_logic_v2.py
   ```

**Bestanden Toevoegen & Committen**

1. `git add`
   Wat doet het: zet wijzigingen klaar voor commit (staging).
   Let op: `git add .` voegt alles toe, ook onbedoelde files.
   Voorbeeld:

   ```bash
   git add src/backend_logic/backend_logic_v2.py
   git add .
   ```

2. `git commit`
   Wat doet het: maakt een snapshot van de gestage wijzigingen.
   Let op: commit liever klein en met duidelijke boodschap.
   Voorbeeld:

   ```bash
   git commit -m "Update laadlogica"
   ```

3. `git commit --amend`
   Wat doet het: past de laatste commit aan (message of inhoud).
   Let op: niet gebruiken als de commit al gepusht is naar shared branch.
   Voorbeeld:
   ```bash
   git commit --amend -m "Update laadlogica en tests"
   ```

**Verschillen**

1. `git diff`
   Wat doet het: toont verschillen tussen working tree en index/HEAD.
   Let op: gebruik `--staged` om te zien wat je gaat committen.
   Voorbeeld:

   ```bash
   git diff
   git diff --staged
   ```

2. `git diff branch`
   Wat doet het: vergelijkt twee branches.
   Let op: `main..feature` toont wat in feature zit maar niet in main.
   Voorbeeld:
   ```bash
   git diff main..feature/charging
   ```

**Branches**

1. `git branch`
   Wat doet het: toont lokale branches.
   Let op: `-a` toont ook remote branches.
   Voorbeeld:

   ```bash
   git branch
   git branch -a
   ```

2. `git switch`
   Wat doet het: wisselt van branch.
   Let op: zorg dat je geen ongestage wijzigingen kwijt raakt.
   Voorbeeld:

   ```bash
   git switch feature/charging
   ```

3. `git checkout`
   Wat doet het: oudere manier om branch te maken/wisselen.
   Let op: `git switch` is veiliger/duidelijker voor branches.
   Voorbeeld:

   ```bash
   git checkout -b feature/charging
   ```

4. `git merge`
   Wat doet het: voegt changes van een branch samen in de huidige branch.
   Let op: kan merge‑conflicten geven die je moet oplossen.
   Voorbeeld:

   ```bash
   git switch main
   git merge feature/charging
   ```

5. `git rebase`
   Wat doet het: herschrijft history door commits “bovenop” een andere branch te zetten.
   Let op: niet gebruiken op branches die al gedeeld/gepusht zijn.
   Voorbeeld:
   ```bash
   git switch feature/charging
   git rebase main
   ```

**Remote & Synchronisatie**

1. `git remote`
   Wat doet het: beheert remote repo‑links.
   Let op: `origin` is een naam, geen vaste URL.
   Voorbeeld:

   ```bash
   git remote -v
   git remote add origin https://github.com/org/repo.git
   ```

2. `git fetch`
   Wat doet het: haalt updates van remote zonder ze te mergen.
   Let op: veilig om te doen, verandert je lokale bestanden niet.
   Voorbeeld:

   ```bash
   git fetch origin
   ```

3. `git pull`
   Wat doet het: haalt updates op én merge/rebase in je huidige branch.
   Let op: kan conflicts veroorzaken; gebruik `git fetch` + `git merge` voor meer controle.
   Voorbeeld:

   ```bash
   git pull origin main
   ```

4. `git push`
   Wat doet het: stuurt je commits naar de remote.
   Let op: push nooit naar `main` zonder team‑afspraak.
   Voorbeeld:
   ```bash
   git push origin feature/charging
   ```

**Undo / Herstel**

1. `git restore`
   Wat doet het: zet bestanden terug naar de laatste commit of index.
   Let op: hierdoor kun je lokale wijzigingen kwijtraken.
   Voorbeeld:

   ```bash
   git restore src/backend_logic/backend_logic_v2.py
   git restore --staged src/backend_logic/backend_logic_v2.py
   ```

2. `git reset`
   Wat doet het: verplaatst de HEAD pointer (commit) en optioneel je staging.
   Let op: `--hard` kan data vernietigen; hier bewust niet opgenomen.
   Voorbeeld:

   ```bash
   git reset --soft HEAD~1
   git reset --mixed HEAD~1
   ```

3. `git revert`
   Wat doet het: maakt een nieuwe commit die een vorige commit ongedaan maakt.
   Let op: veilig voor gedeelde branches.
   Voorbeeld:
   ```bash
   git revert HEAD
   ```

**Stash**

1. `git stash`
   Wat doet het: zet tijdelijke wijzigingen apart zonder commit.
   Let op: stash is lokaal; vergeet niet terug te zetten.
   Voorbeeld:
   ```bash
   git stash
   git stash list
   git stash pop
   ```

**Bestanden Verplaatsen / Verwijderen**

1. `git mv`
   Wat doet het: verplaatst of hernoemt een bestand en houdt git‑tracking intact.
   Let op: liever `git mv` dan een OS rename.
   Voorbeeld:

   ```bash
   git mv src/old.py src/new.py
   ```

2. `git rm`
   Wat doet het: verwijdert bestand en staged de verwijdering.
   Let op: `--cached` verwijdert uit git maar laat lokaal staan.
   Voorbeeld:
   ```bash
   git rm src/old.py
   git rm --cached data/secret.csv
   ```

**Tags**

1. `git tag`
   Wat doet het: markeert een specifieke commit (bv. release).
   Let op: tags worden niet automatisch gepusht.
   Voorbeeld:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

**.gitignore**

1. `git ignore` (via `.gitignore` bestand)
   Wat doet het: voorkomt dat bepaalde bestanden worden toegevoegd.
   Let op: werkt niet retroactief op al getrackte bestanden.
   Voorbeeld:
   ```bash
   echo "data/*.csv" >> .gitignore
   git add .gitignore
   git commit -m "Add gitignore rule for data csv"
   ```

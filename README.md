# SIAE Sport Events Italy Dashboard

Dashboard interattiva sviluppata con Streamlit per l'analisi degli eventi sportivi in Italia nel periodo 2004-2021.

Il progetto analizza l'evoluzione degli spettacoli sportivi registrati in Italia, con focus su distribuzione territoriale, partecipazione del pubblico, dimensione economica e confronto tra regioni e macroaree.

---

## Obiettivo del progetto

La dashboard ha l'obiettivo di fornire una lettura sintetica, comparabile e interattiva dell'evoluzione degli eventi sportivi in Italia.

L'analisi consente di osservare:

- andamento nazionale degli eventi sportivi;
- differenze tra macroaree territoriali;
- ranking regionali;
- distribuzione geografica dei principali indicatori;
- variazioni legate al periodo pandemico;
- dettaglio delle categorie sportive disponibili per il 2021.

---

## Struttura della dashboard

La dashboard è organizzata nelle seguenti sezioni:

### Panoramica nazionale

Sintetizza i principali KPI nazionali disponibili per il 2021:

- totale spettacoli;
- totale persone;
- totale botteghino;
- totale pubblico;
- persone medie per spettacolo;
- botteghino medio per spettacolo;
- variazione YoY;
- indice di resilienza.

### Trend temporali

Mostra l'evoluzione degli indicatori principali nel periodo 2004-2021, con confronto tra macroaree territoriali.

### Ranking regioni

Permette di confrontare le regioni italiane in base all'indicatore selezionato.

### Mappa Italia

Visualizza la distribuzione regionale dei valori attraverso una rappresentazione geografica intuitiva.

### Focus categorie sportive

Approfondisce il dettaglio disponibile per il 2021, distinguendo tra:

- attività sportiva complessiva;
- calcio;
- sport di squadra non calcio;
- sport individuali;
- altri sport.

### Scheda regionale

Consente di analizzare il profilo di una singola regione.

### Tabelle dati

Permette di consultare direttamente le principali basi dati elaborate.

---

## Dataset

Il dataset di riferimento raccoglie informazioni annuali sugli spettacoli sportivi in Italia nel periodo 2004-2021.

I dati sono organizzati per:

- anno;
- territorio;
- livello territoriale;
- categoria sportiva, dove disponibile;
- numero di spettacoli;
- persone partecipanti;
- botteghino;
- pubblico;
- indicatori derivati.

---

## Indicatori principali

La dashboard utilizza i seguenti indicatori:

- numero di spettacoli sportivi;
- persone partecipanti;
- persone medie per spettacolo;
- quota regionale sul totale nazionale;
- botteghino;
- botteghino medio per spettacolo;
- variazione anno su anno;
- indicatori di resilienza post-2020.

---

## Nota metodologica

L'analisi ha finalità descrittiva e comparativa.

I risultati permettono di individuare tendenze, differenze territoriali e dinamiche di partecipazione, ma non devono essere interpretati come evidenza di relazioni causali dirette.

Il periodo 2020-2021 deve essere letto separatamente rispetto agli anni precedenti, a causa della forte discontinuità generata dalla pandemia.

Alcuni indicatori, in particolare quelli economici e quelli legati al dettaglio per categoria sportiva, non sono disponibili con la stessa granularità per tutti gli anni. Per questo motivo, alcune visualizzazioni mostrano esclusivamente le informazioni effettivamente presenti nel dataset.

---

## Tecnologie utilizzate

Il progetto è stato sviluppato con:

- Python;
- Streamlit;
- Pandas;
- Plotly;
- Pydeck o Folium, se utilizzati nella mappa;
- Matplotlib, se utilizzato per visualizzazioni accessorie.

---

## File principali

La repository contiene:

- app.py
- requirements.txt
- README.md
- df_finale_siae_sport.csv
- kpi_cards.csv
- kpi_regioni.csv
- eventuale cartella logosbl con il logo della dashboard

---

## Esecuzione locale

Per eseguire la dashboard localmente:

1. installare le dipendenze con requirements.txt;
2. avviare l'app con Streamlit;
3. aprire il link generato nel browser.

Comando principale:

streamlit run app.py

---

## Deploy su Streamlit Community Cloud

Per pubblicare la dashboard:

1. caricare tutti i file del progetto in una repository GitHub;
2. assicurarsi che app.py e requirements.txt siano presenti nella repository;
3. accedere a Streamlit Community Cloud;
4. selezionare repository, branch e file principale app.py;
5. avviare il deploy.

---

## Output finale

Il risultato finale è una dashboard interattiva consultabile online, pensata per accompagnare l'utente da una panoramica generale del fenomeno a un'analisi più dettagliata per territorio, indicatore e categoria sportiva.

---

## Autore

Progetto realizzato nell'ambito dell'analisi degli eventi sportivi SIAE in Italia.
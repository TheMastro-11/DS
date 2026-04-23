# Report di Analisi: Risoluzione del TSP - MTZ vs Cut Set

## Obiettivo dell'Analisi
Questo documento riassume i risultati del confronto tra due diverse formulazioni matematiche per risolvere il problema del commesso viaggiatore (TSP - Traveling Salesperson Problem) applicato a una mappa reale della città di Cagliari e dintorni. Le due formulazioni testate sono:
1. **MTZ (Miller-Tucker-Zemlin)**
2. **Cut Set (Subtour Elimination / Dantzig-Fulkerson-Johnson)**

## L'Anomalia Rilevata: Da 8 a 800 secondi
Durante l'aggiornamento del codice alla nuova versione, è emersa una forte anomalia nei tempi di risoluzione della formulazione **MTZ**:
* **Versione Precedente:** Il solutore ha trovato la soluzione ottima in circa **8 secondi**.
* **Nuova Versione:** Il solutore ha raggiunto il limite di tempo massimo impostato (**800 secondi**) senza riuscire a confermare l'ottimalità della soluzione.

Al contrario, la formulazione **Cut Set** ha mantenuto tempi di risoluzione eccellenti (pochi secondi) in entrambe le versioni del codice.

## La Causa: La Scelta del Deposito
L'analisi del codice ha rivelato che il drastico calo di prestazioni dell'MTZ non era dovuto a un bug di programmazione, ma a una singola, cruciale modifica logica: **il nodo di partenza (deposito)**.

* **Caso Veloce (Vecchio Codice):** Il punto di partenza di default era il *Bastione Saint Remy* (Nodo 0). Essendo un punto estremamente **centrale** rispetto agli altri nodi da visitare, le distanze iniziali erano bilanciate.
* **Caso Lento (Nuovo Codice):** Il punto di partenza è stato impostato correttamente sul *Deposito di Via S. Paolo* (Nodo 28). Questo punto è **periferico** e asimmetrico rispetto alla maggior parte degli altri nodi.

## Spiegazione Tecnica (Il "Dietro le Quinte")
Perché la posizione del deposito ha un impatto così devastante sull'MTZ ma non sul Cut Set? La risposta risiede nella matematica alla base dei due modelli.

### 1. La debolezza del modello MTZ
In Ricerca Operativa, si dice che la formulazione MTZ ha un **"rilassamento continuo debole"**. Questo significa che, prima di trovare la soluzione a numeri interi (il percorso reale), il computer "rilassa" le regole esplorando percorsi frazionari (es. percorre mezza strada). 
Poiché la formula matematica dell'MTZ non restringe bene queste opzioni frazionarie, il solutore si affida pesantemente alle sue *euristiche* (il suo intuito interno) per indovinare rapidamente una buona strada. 
* Se si parte dal centro (vecchio codice), l'intuito del solutore funziona bene.
* Se si parte dalla periferia (nuovo codice), l'asimmetria delle distanze inganna l'intuito del solutore, costringendolo a esplorare milioni di percorsi sub-ottimali (esplosione dell'albero di Branch & Bound), esaurendo il tempo a disposizione.

### 2. La forza del modello Cut Set
La formulazione Cut Set affronta il problema in modo radicalmente diverso: valuta la rete nel suo insieme e "taglia" letteralmente via i percorsi chiusi non validi (i sottotour) mano a mano che si presentano. Questo approccio garantisce un **"rilassamento continuo molto forte"**. Al Cut Set non importa da dove si inizia: la struttura matematica guida il solutore in modo rigido e infallibile verso la soluzione ottima in pochissimo tempo.

## Conclusione e Best Practices
Questo caso di studio dimostra empiricamente una delle leggi fondamentali dell'ottimizzazione su reti: **la formulazione MTZ è altamente instabile e sensibile ai dati di input**.

**Regole d'oro per lo sviluppo futuro:**
* Per problemi TSP e VRP (Vehicle Routing Problem) nel mondo reale, la formulazione **Cut Set (con Callback)** è sempre da preferire per la sua robustezza e velocità.
* L'MTZ rimane utile a scopo didattico, ma non è adatto per la messa in produzione su mappe reali con distribuzioni asimmetriche dei punti di consegna.
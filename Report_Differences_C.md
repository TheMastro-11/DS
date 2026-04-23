# Analisi: Perché MTZ impiega 300 s nel nuovo codice vs ~8 s nel vecchio?

## Risposta breve

Non c'è un bug. La differenza è causata da **due fattori combinati**: un cambio strutturale nell'istanza del problema e la natura intrinsecamente instabile di MTZ su istanze di 50 nodi.

---

## 1. Il `set_time_limit(300)` c'è in entrambi i file

È facile sospettare che il timeout sia stato introdotto nel nuovo codice, ma guardando entrambe le versioni si vede che la riga è identica:

```python
# tsp_MTZ_CS_old.py  (riga 365)
mdl_mtz_int.set_time_limit(300)

# tsp_MTZ_CS.py  (riga 614)
mdl_mtz_int.set_time_limit(300)
```

Il timeout non è la causa — è solo il limite che il nuovo codice raggiunge, mentre il vecchio terminava prima.

---

## 2. Il cambio rilevante: `cities[1:]` → `cities_non_depot`

### Vecchio codice (`tsp_MTZ_CS_old.py`, righe 333–336)

```python
for i in cities[1:]:   # esclude sempre il nodo con indice 0
    for j in cities[1:]:
        if i != j:
            mdl_mtz.add_constraint(u[i] - u[j] + n * x[(i, j)] <= n - 1)
```

### Nuovo codice (`tsp_MTZ_CS.py`, righe 581–585)

```python
cities_non_depot = [i for i in cities if i != depot_id]
for i in cities_non_depot:   # esclude il nodo del deposito per nome
    for j in cities_non_depot:
        if i != j:
            mdl_mtz.add_constraint(u[i] - u[j] + n * x[(i, j)] <= n - 1)
```

A prima vista sembrano equivalenti — e **logicamente lo sono** — perché in entrambi i casi il deposito si trova all'indice 0. La differenza è che nel nuovo codice il deposito è stato **spostato in cima alla lista** come primo elemento consapevolmente designato, mentre nel vecchio era lì per caso (il nodo 0 era "Bastione Saint Remy", non un deposito reale).

---

## 3. La vera causa: cambio di istanza

Il vero motivo per cui le performance divergono è che **l'istanza del problema è cambiata**:

| Aspetto | Vecchio codice | Nuovo codice |
|---|---|---|
| Nodo 0 | Bastione Saint Remy | **Deposito (Via S. Paolo)** |
| Posizione deposito | Implicita (nodo 0 per caso) | Esplicita (primo elemento della lista) |
| Matrice distanze | Basata sulle coords del vecchio nodo 0 | Basata sulle coords del deposito reale |

Cambiare il nodo di partenza modifica completamente la matrice di distanze ORS, e quindi la struttura dell'albero Branch & Bound che CPLEX deve esplorare.

---

## 4. Perché MTZ è instabile su 50 nodi?

MTZ introduce **O(n²) vincoli** di eliminazione subtour già nel rilassamento LP:

$$u_i - u_j + n \cdot x_{ij} \leq n - 1 \quad \forall i,j \in V \setminus \{0\}, \ i \neq j$$

Con n = 50, questo significa **~2.400 vincoli aggiuntivi** rispetto alla formulazione Cut Set. Questi vincoli però producono un **rilassamento LP molto debole**: il gap tra il bound continuo e la soluzione intera ottima è grande, e l'albero Branch & Bound che CPLEX deve esplorare può diventare enormemente più grande al variare dell'istanza.

```
Gap MTZ ≫ Gap Cut Set
     ↓
Albero B&B molto più profondo
     ↓
Tempo di risoluzione altamente variabile (da secondi a timeout)
```

La formulazione Cut Set, al contrario, aggiunge tagli solo dove servono (sui subtour effettivamente violati), mantenendo un bound LP molto più stretto.

---

## 5. Conclusione

Il vecchio codice "sembrava" veloce su MTZ perché:
1. L'istanza specifica (con "Bastione Saint Remy" come nodo 0) produceva un albero B&B fortunatamente piccolo.
2. Potenzialmente beneficiava di un warm start implicito dopo l'esecuzione del Cut Set.

Il nuovo codice **non è più lento per un bug** — espone semplicemente il limite strutturale di MTZ su istanze di questa dimensione. Per risolvere in modo affidabile 50 nodi entro tempi ragionevoli, la formulazione Cut Set (o Cut Set con callbacks CPLEX) è la scelta corretta.

---

*Analisi generata confrontando `tsp_MTZ_CS_old.py` e `tsp_MTZ_CS.py`*

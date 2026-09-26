# AI Arbitrage Agent

Aplikacja Streamlit do:
- monitorowania **boxów ze zwrotów** (Olimibox, Returnstore) + linki Amazon.pl
- skanowania okazji na **OLX**
- prowadzenia **ewidencji sprzedaży** (działalność nierejestrowana, limit kwartalny 2026)

## Deploy na Streamlit Cloud (zalecane)

1. Wrzuć **całą zawartość tego folderu** do repozytorium GitHub.
2. Wejdź na [https://share.streamlit.io](https://share.streamlit.io)
3. New app → wybierz repo → **Main file path:** `app.py`
4. Deploy.

Aplikacja działa bez kluczy API. OLX + boxy Olimibox/Returnstore są aktywne od razu.

## Uruchomienie lokalne

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Zakładki

| Zakładka | Opis |
|----------|------|
| **Boxy** | Śledzone URL (Box Mix A, ElectroBox) + listingi + linki Amazon |
| **Skaner OLX** | Tanie oferty pod odsprzedaż |
| **Ewidencja sprzedaży** | Lp., data, wartość należna, suma kwartalna (limit 10 813,50 zł) |
| **O aplikacji** | Instrukcje i limity prawne |

## Ewidencja (działalność nierejestrowana)

Obowiązkowe pola: numer porządkowy, data sprzedaży, wartość należna, suma narastająco w kwartale.  
Dane w sesji przeglądarki – regularnie pobieraj CSV/JSON.

## Wymagania

- Python 3.11+
- `requirements.txt` + `packages.txt` (lxml) pod Streamlit Cloud

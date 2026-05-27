# Chatbot AI - Progetto di Maturità

Progetto realizzato da **Mattia Di Carlo**.

## Cosa contiene

- Backend Flask in `app.py`
- Frontend HTML, CSS e JavaScript nella cartella `frontend/`
- Interfaccia chiara stile ChatGPT, pulita, moderna e responsive
- Modalità normale per risposte chiare, complete e adatte all'orale
- Modalità **Pirandello 2.0** per risposte più discorsive, letterarie e collegate al tema dell'identità
- Risposta personalizzata alla domanda: "Chi è il tuo creatore?"
- Memoria breve della conversazione, così il chatbot mantiene meglio il contesto
- Limiti di risposta aumentati per evitare che i discorsi si interrompano a metà

## Avvio locale rapido

Entra nella cartella del progetto:

```bash
cd chatbot-ai
```

Installa le dipendenze:

```bash
pip install -r requirements.txt
```

Imposta la chiave Gemini.

Su macOS/Linux:

```bash
export API_KEY="LA_TUA_CHIAVE_GEMINI"
```

Su Windows PowerShell:

```powershell
$env:API_KEY="LA_TUA_CHIAVE_GEMINI"
```

Avvia il progetto:

```bash
python app.py
```

Poi apri il browser su:

```text
http://localhost:10000
```

## Deploy consigliato su Render

Build Command:

```bash
pip install -r requirements.txt
```

Start Command:

```bash
gunicorn app:app
```

Variabile d'ambiente da aggiungere su Render:

```text
API_KEY = LA_TUA_CHIAVE_GEMINI
```

Non inserire mai la chiave API dentro il codice e non caricarla mai su GitHub.

## Aggiornare GitHub dopo una modifica

Dentro la cartella del progetto:

```bash
git status
git add .
git commit -m "Aggiorna chatbot AI"
git push origin main
```

Se GitHub rifiuta il push perché avevi cancellato o modificato file online:

```bash
git fetch origin
git push origin main --force-with-lease
```

## File utili

- `PRESENTAZIONE_ORALE.md`: traccia per spiegare il progetto alla commissione
- `GUIDA_AVVIO_GITHUB_RENDER.md`: guida completa per avvio locale, GitHub e Render

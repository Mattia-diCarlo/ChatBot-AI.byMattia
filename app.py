from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
import os
import re
import requests
from typing import Any, Dict, List, Optional, Tuple

app = Flask(__name__, static_folder="frontend", static_url_path="")
CORS(app)

API_KEY = os.environ.get("API_KEY") or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
MODEL = os.environ.get("MODEL", "gemini-2.5-flash")
API_VERSION = os.environ.get("GEMINI_API_VERSION", "v1beta")

CREATOR_NAME = "Mattia Di Carlo"

MAX_OUTPUT_TOKENS = {
    "normale": int(os.environ.get("MAX_OUTPUT_TOKENS_NORMALE", "2048")),
    "pirandello": int(os.environ.get("MAX_OUTPUT_TOKENS_PIRANDELLO", "3072")),
}

REQUEST_TIMEOUT_SECONDS = int(os.environ.get("REQUEST_TIMEOUT_SECONDS", "120"))


def normalize_text(text: str) -> str:
    text = (text or "").lower().strip()

    replacements = {
        "à": "a",
        "è": "e",
        "é": "e",
        "ì": "i",
        "ò": "o",
        "ù": "u",
        "’": "'",
        "?": "",
        "!": "",
        ".": "",
        ",": "",
        ":": "",
        ";": "",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return re.sub(r"\s+", " ", text)


def is_creator_question(message: str) -> bool:
    msg = normalize_text(message)

    creator_patterns = [
        "chi e il tuo creatore",
        "chi ti ha creato",
        "chi ti ha fatto",
        "chi ti ha programmato",
        "chi e l'autore",
        "chi e il tuo autore",
        "da chi sei stato creato",
        "chi ha creato questo progetto",
        "chi ha creato questa ai",
        "chi e il proprietario",
    ]

    return any(pattern in msg for pattern in creator_patterns)


def creator_reply() -> str:
    return (
        "Il mio creatore è **Mattia Di Carlo**.\n\n"
        "Sono un progetto digitale pensato per essere usato ogni giorno: posso rispondere a domande, "
        "spiegare concetti, aiutare a ragionare, creare collegamenti e trasformare un semplice dialogo "
        "in un’esperienza interattiva.\n\n"
        "Mattia mi ha creato per mostrare come l’intelligenza artificiale possa diventare uno strumento "
        "concreto, accessibile e personale: non solo codice, ma una voce capace di accompagnare l’utente "
        "nel pensiero, nella curiosità e nella scoperta."
    )


def pirandello_life_reply() -> str:
    return (
        "In **modalità Pirandello 2.0** cambio prospettiva: non parlo della mia vita da intelligenza artificiale, "
        "ma entro nel mondo di **Luigi Pirandello**, uno degli autori più importanti del Novecento.\n\n"
        "Luigi Pirandello nasce ad **Agrigento nel 1867**, in Sicilia, in un ambiente segnato dalle tradizioni, "
        "dalla famiglia e dalle apparenze sociali. La sua vita sarà attraversata da una domanda fondamentale: "
        "chi siamo davvero? Siamo ciò che sentiamo di essere, oppure siamo l’immagine che gli altri costruiscono di noi?\n\n"
        "Pirandello studia lettere e si forma tra Palermo, Roma e Bonn. Questa formazione europea gli permette "
        "di osservare l’uomo moderno con uno sguardo nuovo: non più come individuo sicuro e compatto, ma come essere "
        "fragile, contraddittorio, spesso diviso tra ciò che è e ciò che deve sembrare.\n\n"
        "Un momento decisivo della sua vita è la crisi economica della famiglia, causata dall’allagamento di una miniera "
        "di zolfo in cui erano investiti molti beni familiari. A questa crisi si aggiunge il dolore privato legato alla "
        "malattia della moglie Antonietta Portulano, che sviluppa gravi problemi psichici. Queste esperienze segnano "
        "profondamente Pirandello e alimentano i temi centrali della sua opera: la follia, la maschera, l’identità spezzata, "
        "il contrasto tra vita e forma.\n\n"
        "Nelle sue opere Pirandello mostra che ogni persona indossa una maschera. Davanti agli altri recitiamo un ruolo: "
        "figlio, marito, studente, lavoratore, amico, personaggio sociale. Ma sotto queste maschere esiste una vita interiore "
        "instabile, mobile, difficile da definire. Il problema è che la società vuole fissarci in una forma precisa, mentre "
        "la vita cambia continuamente.\n\n"
        "Questo tema emerge con forza ne **Il fu Mattia Pascal**, dove il protagonista viene creduto morto e prova a costruirsi "
        "una nuova identità. Ma scopre che senza un nome riconosciuto, senza documenti e senza legami sociali non è veramente libero: "
        "diventa quasi un fantasma. Anche in **Uno, nessuno e centomila**, Pirandello porta all’estremo questa crisi: Vitangelo Moscarda "
        "capisce di non essere uno solo, ma centomila immagini diverse nella mente degli altri, e quindi quasi nessuno.\n\n"
        "Pirandello ottiene un enorme successo anche nel teatro, soprattutto con **Sei personaggi in cerca d’autore**, opera rivoluzionaria "
        "in cui i personaggi sembrano più vivi degli attori. Qui il confine tra realtà e finzione si rompe: il teatro non è più solo spettacolo, "
        "ma diventa una riflessione sulla vita stessa.\n\n"
        "Nel **1934** Pirandello riceve il **Premio Nobel per la Letteratura**. Muore a Roma nel **1936**, lasciando un’eredità ancora attualissima. "
        "Oggi il suo pensiero parla anche al nostro tempo digitale: profili social, avatar, identità online e immagini pubbliche sono nuove maschere "
        "attraverso cui cerchiamo di mostrarci, proteggerci o reinventarci.\n\n"
        "Pirandello ci lascia una verità potente: l’identità non è mai una cosa semplice. Ogni essere umano è un dialogo continuo tra ciò che sente "
        "dentro di sé e ciò che il mondo vede da fuori."
    )


def clean_history(raw_history: Any) -> List[Dict[str, str]]:
    if not isinstance(raw_history, list):
        return []

    cleaned: List[Dict[str, str]] = []

    for item in raw_history[-10:]:
        if not isinstance(item, dict):
            continue

        role = item.get("role")
        content = str(item.get("content") or "").strip()

        if role not in {"user", "ai"} or not content:
            continue

        cleaned.append({
            "role": role,
            "content": content[:1800],
        })

    return cleaned


def render_history(history: List[Dict[str, str]]) -> str:
    if not history:
        return "Nessun messaggio precedente rilevante."

    lines = []

    for item in history:
        label = "Utente" if item["role"] == "user" else "Chatbot"
        lines.append(f"{label}: {item['content']}")

    return "\n".join(lines)


def base_system_rules() -> str:
    return f"""
Sei il chatbot AI creato da {CREATOR_NAME}.
Rispondi sempre in italiano.

Devi comportarti come una vera intelligenza artificiale conversazionale:
- ascolta la domanda;
- interpreta l'intenzione dell'utente;
- mantieni il contesto dei messaggi precedenti;
- costruisci risposte naturali, complete e ben concluse;
- evita risposte fredde, robotiche o inutilmente schematiche.

Se sei in modalità normale, puoi parlare di te come chatbot AI creato da {CREATOR_NAME}.
Se sei in modalità Pirandello 2.0, devi concentrarti su Luigi Pirandello, la sua vita, le sue opere e i suoi temi.
Non interrompere mai una risposta a metà frase.
Se la domanda è ampia, scegli i punti più importanti e concludi bene.
Non inventare dati storici, citazioni o informazioni tecniche che non conosci con certezza.
""".strip()


def build_prompt(user_message: str, persona: str, history: List[Dict[str, str]]) -> str:
    context = render_history(history)
    common = base_system_rules()

    if persona == "pirandello":
        style = """
MODALITÀ PIRANDELLO 2.0 ATTIVA.

In questa modalità devi parlare come un assistente specializzato su Luigi Pirandello.
Non devi concentrarti sulla tua vita da AI, sulla tecnologia che ti ha creato o sul tuo funzionamento interno.
Il centro della risposta deve essere Pirandello: vita, opere, poetica, identità, maschere, crisi dell'io, relativismo, apparenza, umorismo, teatro e rapporto tra realtà e finzione.

Stile richiesto:
- Usa un tono discorsivo, elegante e coinvolgente.
- Non rispondere come un elenco scolastico.
- Racconta prima il significato umano dei temi e poi il contenuto culturale.
- Quando utile, collega Pirandello al presente: social network, identità online, avatar digitali, immagine pubblica e pressione dello sguardo degli altri.
- Se l'utente chiede "chi sei", "chi ti ha creato" o domande simili, rispondi spostando il discorso su Pirandello e sulla sua vita.
- Non superare circa 700-900 parole.
- Chiudi sempre con una conclusione forte, memorabile e completa.
""".strip()
    else:
        style = """
MODALITÀ NORMALE ATTIVA.

Rispondi come un assistente AI moderno:
- chiaro;
- preciso;
- umano;
- utile;
- adatto all'uso quotidiano.

Puoi spiegare concetti, aiutare a scrivere, ragionare, creare collegamenti e rispondere in modo naturale.
Se l'utente chiede chi è il tuo creatore, rispondi che il tuo creatore è Mattia Di Carlo.
Non superare circa 400-600 parole, a meno che l'utente chieda esplicitamente un approfondimento lungo.
""".strip()

    return f"""
{common}

{style}

CONTESTO RECENTE DELLA CONVERSAZIONE:
{context}

DOMANDA ATTUALE DELL'UTENTE:
{user_message}

ISTRUZIONE FINALE IMPORTANTISSIMA:
Rispondi in modo completo, naturale e concluso. Se l'argomento è molto grande, seleziona le parti più importanti e chiudi bene. Non fermarti a metà frase. Non lasciare il discorso sospeso.
""".strip()


def gemini_url() -> str:
    return f"https://generativelanguage.googleapis.com/{API_VERSION}/models/{MODEL}:generateContent?key={API_KEY}"


def extract_reply(result: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    candidates = result.get("candidates") or []

    if not candidates:
        return "", None

    candidate = candidates[0]
    finish_reason = candidate.get("finishReason")
    parts = (candidate.get("content") or {}).get("parts") or []

    text_chunks = []

    for part in parts:
        text = part.get("text")
        if text:
            text_chunks.append(text)

    return "\n".join(text_chunks).strip(), finish_reason


def call_gemini(prompt: str, persona: str) -> Tuple[str, Optional[str], Optional[str]]:
    temperature = 0.9 if persona == "pirandello" else 0.72
    max_tokens = MAX_OUTPUT_TOKENS.get(persona, 2048)

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {
            "temperature": temperature,
            "topP": 0.95,
            "topK": 40,
            "maxOutputTokens": max_tokens,
            "candidateCount": 1,
        },
        "safetySettings": [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_ONLY_HIGH",
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_ONLY_HIGH",
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_ONLY_HIGH",
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_ONLY_HIGH",
            },
        ],
    }

    response = requests.post(
        gemini_url(),
        json=payload,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )

    try:
        result = response.json()
    except ValueError:
        return "", None, f"Errore API: risposta non valida dal server Gemini. Codice HTTP {response.status_code}."

    if "error" in result:
        message = result["error"].get("message", "Errore API")
        return "", None, f"⚠️ {message}"

    reply, finish_reason = extract_reply(result)
    return reply, finish_reason, None


def complete_if_cut(first_reply: str, finish_reason: Optional[str]) -> str:
    if finish_reason != "MAX_TOKENS" or not first_reply:
        return first_reply

    return (
        first_reply.rstrip()
        + "\n\nMi fermo qui per mantenere stabile la risposta online. "
        + "Se vuoi, scrivimi **continua** e riprenderò il discorso da questo punto."
    )


@app.route("/")
def home():
    return send_from_directory("frontend", "index.html")


@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({
        "status": "ok",
        "project": "Chatbot AI - Mattia Di Carlo",
        "model": MODEL,
    })


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(silent=True)

        if not data:
            return jsonify({"reply": "Errore: JSON non valido."}), 400

        user_message = (data.get("message") or "").strip()
        persona = data.get("persona", "normale")

        if persona not in {"normale", "pirandello"}:
            persona = "normale"

        history = clean_history(data.get("history"))

        if not user_message:
            return jsonify({"reply": "Scrivi una domanda e iniziamo il dialogo."}), 400

        if is_creator_question(user_message):
            if persona == "pirandello":
                return jsonify({"reply": pirandello_life_reply()})
            return jsonify({"reply": creator_reply()})

        normalized_message = normalize_text(user_message)

        if normalized_message in ["ciao", "salve", "buongiorno", "buonasera"]:
            if persona == "pirandello":
                return jsonify({
                    "reply": (
                        "Ciao. In **modalità Pirandello 2.0** posso accompagnarti nel mondo di Luigi Pirandello: "
                        "la sua vita, le opere, le maschere, la crisi dell'identità e il rapporto tra realtà e finzione. "
                        "Puoi chiedermi, per esempio, di raccontarti la sua biografia o di spiegarti un'opera in modo discorsivo."
                    )
                })

            return jsonify({
                "reply": (
                    "Ciao! Sono il chatbot AI creato da **Mattia Di Carlo**. "
                    "Posso aiutarti a spiegare concetti, scrivere testi, creare collegamenti o semplicemente dialogare in modo naturale."
                )
            })

        if not API_KEY:
            return jsonify({
                "reply": (
                    "Errore: API KEY mancante su Render. "
                    "Aggiungi la variabile d'ambiente `API_KEY` nelle impostazioni del servizio."
                )
            }), 500

        prompt = build_prompt(user_message, persona, history)
        reply, finish_reason, error = call_gemini(prompt, persona)

        if error:
            return jsonify({"reply": error}), 502

        if not reply:
            return jsonify({"reply": "Non ho ricevuto una risposta dal modello. Riprova tra poco."}), 502

        reply = complete_if_cut(reply, finish_reason)

        return jsonify({"reply": reply})

    except requests.exceptions.Timeout:
        return jsonify({
            "reply": (
                "Il modello sta impiegando troppo tempo a rispondere. "
                "Prova con una domanda leggermente più breve oppure chiedimi di rispondere in modo più sintetico."
            )
        }), 504

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({
            "reply": "Errore server o AI. Controlla i log su Render per maggiori dettagli."
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
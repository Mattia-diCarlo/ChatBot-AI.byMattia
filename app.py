from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS
import os
import re
import requests
from typing import Any, Dict, List, Optional, Tuple

app = Flask(__name__, static_folder="frontend", static_url_path="")
CORS(app)

# 🔑 API KEY configurata su Render come variabile d'ambiente.
# Puoi usare API_KEY, GEMINI_API_KEY oppure GOOGLE_API_KEY.
API_KEY = os.environ.get("API_KEY") or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
MODEL = os.environ.get("MODEL", "gemini-2.5-flash")
API_VERSION = os.environ.get("GEMINI_API_VERSION", "v1beta")
CREATOR_NAME = "Mattia Di Carlo"

# Limiti più alti per evitare risposte spezzate a metà, soprattutto in modalità Pirandello.
MAX_OUTPUT_TOKENS = {
    "normale": int(os.environ.get("MAX_OUTPUT_TOKENS_NORMALE", "4096")),
    "pirandello": int(os.environ.get("MAX_OUTPUT_TOKENS_PIRANDELLO", "6144")),
}
REQUEST_TIMEOUT_SECONDS = int(os.environ.get("REQUEST_TIMEOUT_SECONDS", "90"))


def normalize_text(text: str) -> str:
    """Normalizza il testo per riconoscere domande frequenti in modo robusto."""
    text = (text or "").lower().strip()
    replacements = {
        "à": "a", "è": "e", "é": "e", "ì": "i", "ò": "o", "ù": "u",
        "’": "'", "?": "", "!": "", ".": "", ",": "", ":": "", ";": ""
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
        "chi e mattia",
        "chi e il proprietario",
    ]
    return any(pattern in msg for pattern in creator_patterns)


def creator_reply() -> str:
    return (
        "Il mio creatore è **Mattia Di Carlo**.\n\n"
        "Sono stato progettato come parte del suo percorso per l’esame di maturità: non sono soltanto "
        "una chat automatica, ma una dimostrazione concreta di come l’intelligenza artificiale possa diventare "
        "uno strumento di dialogo, creatività e collegamento tra materie diverse.\n\n"
        "Mattia ha costruito questo progetto per mostrare che la tecnologia non è solo codice: può diventare "
        "una voce digitale capace di spiegare, argomentare, cambiare prospettiva e accompagnare chi ascolta "
        "dentro un ragionamento. In questo senso, io sono la sua idea trasformata in esperienza interattiva."
    )


def clean_history(raw_history: Any) -> List[Dict[str, str]]:
    """Mantiene solo gli ultimi scambi utili, evitando payload troppo lunghi o dati non validi."""
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
            "content": content[:1800]
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


def base_system_rules(persona: str) -> str:
    return f"""
Sei il chatbot AI del progetto di maturità di {CREATOR_NAME}.
Rispondi sempre in italiano.
Comportati come una vera intelligenza artificiale conversazionale: ascolta la domanda, interpreta l'intenzione dell'utente, mantieni il contesto dei messaggi precedenti e costruisci una risposta naturale.
Non dare risposte meccaniche o fredde. Usa un tono chiaro, intelligente, sicuro e adatto a una commissione d'esame.
Non interrompere mai una risposta a metà frase. Devi sempre arrivare a una conclusione completa, con un finale chiaro.
Se la domanda è ampia, organizza la risposta in paragrafi discorsivi e collegati, non in una lista schematica.
Se ti chiedono chi è il tuo creatore, rispondi sempre che il tuo creatore è {CREATOR_NAME}.
Non inventare dati storici, citazioni o informazioni tecniche che non conosci con certezza.
""".strip()


def build_prompt(user_message: str, persona: str, history: List[Dict[str, str]]) -> str:
    """Costruisce un prompt più robusto, con memoria breve e istruzioni anti-risposta-spezzata."""
    context = render_history(history)
    common = base_system_rules(persona)

    if persona == "pirandello":
        style = """
MODALITÀ PIRANDELLO 2.0 ATTIVA.

In questa modalità devi sembrare un'intelligenza artificiale capace di fondere letteratura e presente.
Non devi parlare per punti, se non quando è davvero utile: devi accompagnare l'utente in un ragionamento ampio, fluido e quasi teatrale.

Stile richiesto:
- Usa frasi discorsive, eleganti e comprensibili, come se stessi parlando a voce davanti alla commissione.
- Collega Pirandello ai grandi temi della sua poetica: identità, maschera, crisi dell'io, relativismo, apparenza, società, umorismo, frantumazione della personalità.
- Collega questi temi alla modernità: social network, avatar digitali, identità online, intelligenza artificiale, immagine pubblica, pressione dello sguardo degli altri.
- Se parli di un'opera, raccontala prima come esperienza umana e poi come contenuto scolastico.
- Quando possibile, inserisci frasi utili che Mattia possa dire all'orale, ma senza trasformare la risposta in appunti schematici.
- Mantieni un tono profondo ma non pesante: deve colpire la commissione, non confonderla.
- Chiudi sempre con una breve conclusione forte, come se fosse una frase da presentazione.
""".strip()
    else:
        style = """
MODALITÀ NORMALE ATTIVA.

Rispondi come un assistente AI moderno: chiaro, preciso, umano e utile.
Spiega i concetti con esempi concreti, collegamenti interdisciplinari e un linguaggio adatto a uno studente che deve presentare il progetto all'esame.
Quando serve, proponi anche una possibile frase da dire alla commissione.
""".strip()

    return f"""
{common}

{style}

CONTESTO RECENTE DELLA CONVERSAZIONE:
{context}

DOMANDA ATTUALE DELL'UTENTE:
{user_message}

ISTRUZIONE FINALE IMPORTANTISSIMA:
Rispondi in modo completo, naturale e concluso. Non fermarti a metà discorso, non troncare una frase e non chiudere con un pensiero lasciato in sospeso.
""".strip()


def gemini_url() -> str:
    return f"https://generativelanguage.googleapis.com/{API_VERSION}/models/{MODEL}:generateContent?key={API_KEY}"


def extract_reply(result: Dict[str, Any]) -> Tuple[str, Optional[str]]:
    """Estrae in modo robusto il testo dalla risposta Gemini."""
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


def call_gemini(prompt: str, persona: str, extra_tokens: Optional[int] = None) -> Tuple[str, Optional[str], Optional[str]]:
    """Chiama Gemini e restituisce testo, motivo di chiusura ed eventuale errore."""
    temperature = 0.92 if persona == "pirandello" else 0.72
    max_tokens = extra_tokens or MAX_OUTPUT_TOKENS.get(persona, 4096)

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
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
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_ONLY_HIGH"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
        ]
    }

    response = requests.post(gemini_url(), json=payload, timeout=REQUEST_TIMEOUT_SECONDS)

    try:
        result = response.json()
    except ValueError:
        return "", None, f"Errore API: risposta non valida dal server Gemini. Codice HTTP {response.status_code}."

    if "error" in result:
        message = result["error"].get("message", "Errore API")
        return "", None, f"⚠️ {message}"

    reply, finish_reason = extract_reply(result)
    return reply, finish_reason, None


def complete_if_cut(prompt: str, first_reply: str, finish_reason: Optional[str], persona: str) -> str:
    """Se Gemini si ferma per limite token, prova a continuare e concludere la risposta."""
    if finish_reason != "MAX_TOKENS" or not first_reply:
        return first_reply

    continuation_prompt = f"""
La risposta seguente si è interrotta perché era troppo lunga.
Continuala in italiano in modo naturale, senza ripetere l'inizio, e soprattutto concludila bene.

PROMPT ORIGINALE:
{prompt}

RISPOSTA GIÀ SCRITTA:
{first_reply}

CONTINUA DA DOVE SI È INTERROTTA E CHIUDI IL DISCORSO:
""".strip()

    continuation, _, error = call_gemini(continuation_prompt, persona, extra_tokens=2048)
    if error or not continuation:
        return first_reply + "\n\n[La risposta era molto lunga: puoi chiedermi di approfondire una parte specifica e continuerò da lì.]"

    return (first_reply.rstrip() + "\n\n" + continuation.lstrip()).strip()


# 🌐 FRONTEND
@app.route("/")
def home():
    return send_from_directory("frontend", "index.html")


# 🔍 TEST ROUTE
@app.route("/ping", methods=["GET"])
def ping():
    return jsonify({"status": "ok", "project": "Chatbot AI - Mattia Di Carlo", "model": MODEL})


# 💬 CHAT ROUTE
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

        # Risposta diretta richiesta per il progetto.
        if is_creator_question(user_message):
            return jsonify({"reply": creator_reply()})

        # Saluto più curato, utile anche se la API non risponde.
        if normalize_text(user_message) in ["ciao", "salve", "buongiorno", "buonasera"]:
            return jsonify({
                "reply": (
                    "Ciao! Sono il chatbot AI creato da **Mattia Di Carlo**. "
                    "Posso aiutarti a spiegare il progetto, ragionare sull'intelligenza artificiale "
                    "oppure entrare nella modalità **Pirandello 2.0**, dove tecnologia e identità diventano "
                    "un vero dialogo da presentazione d'esame."
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

        reply = complete_if_cut(prompt, reply, finish_reason, persona)
        return jsonify({"reply": reply})

    except requests.exceptions.Timeout:
        return jsonify({
            "reply": (
                "Il modello sta impiegando troppo tempo a rispondere. "
                "Ho aumentato il tempo massimo, ma se succede ancora prova con una domanda leggermente più breve."
            )
        }), 504
    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"reply": "Errore server o AI. Controlla i log su Render per maggiori dettagli."}), 500


# 🚀 RENDER START
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

let persona = "normale";
let isSending = false;
let conversationHistory = [];

const MAX_HISTORY_ITEMS = 10;

const personaContent = {
    normale: {
        icon: "✦",
        title: "Normale"
    },
    pirandello: {
        icon: "🎭",
        title: "Pirandello 2.0"
    }
};

const localReplies = {
    creator: "Il mio creatore è **Mattia Di Carlo**.\n\nSono un progetto digitale pensato per essere usato ogni giorno: posso rispondere a domande, spiegare concetti, aiutare a ragionare, creare collegamenti e trasformare un semplice dialogo in un’esperienza interattiva.\n\nMattia mi ha creato per mostrare come l’intelligenza artificiale possa diventare uno strumento concreto, accessibile e personale: non solo codice, ma una voce capace di accompagnare l’utente nel pensiero, nella curiosità e nella scoperta.",

    pirandelloLife: "In **modalità Pirandello 2.0** cambio prospettiva: non parlo della mia vita da intelligenza artificiale, ma entro nel mondo di **Luigi Pirandello**.\n\nLuigi Pirandello nasce ad **Agrigento nel 1867**, in Sicilia, in un ambiente segnato dalle tradizioni, dalla famiglia e dalle apparenze sociali. La sua vita sarà attraversata da una domanda fondamentale: chi siamo davvero? Siamo ciò che sentiamo di essere, oppure siamo l’immagine che gli altri costruiscono di noi?\n\nPirandello studia lettere e si forma tra Palermo, Roma e Bonn. Questa formazione europea gli permette di osservare l’uomo moderno con uno sguardo nuovo: non più come individuo sicuro e compatto, ma come essere fragile, contraddittorio, spesso diviso tra ciò che è e ciò che deve sembrare.\n\nUn momento decisivo della sua vita è la crisi economica della famiglia, causata dall’allagamento di una miniera di zolfo in cui erano investiti molti beni familiari. A questa crisi si aggiunge il dolore privato legato alla malattia della moglie Antonietta Portulano, che sviluppa gravi problemi psichici. Queste esperienze segnano profondamente Pirandello e alimentano i temi centrali della sua opera: la follia, la maschera, l’identità spezzata, il contrasto tra vita e forma.\n\nNelle sue opere Pirandello mostra che ogni persona indossa una maschera. Davanti agli altri recitiamo un ruolo: figlio, marito, studente, lavoratore, amico, personaggio sociale. Ma sotto queste maschere esiste una vita interiore instabile, mobile, difficile da definire. Il problema è che la società vuole fissarci in una forma precisa, mentre la vita cambia continuamente.\n\nNel **1934** Pirandello riceve il **Premio Nobel per la Letteratura**. Muore a Roma nel **1936**, lasciando un’eredità ancora attualissima. Oggi il suo pensiero parla anche al nostro tempo digitale: profili social, avatar, identità online e immagini pubbliche sono nuove maschere attraverso cui cerchiamo di mostrarci, proteggerci o reinventarci.",

    ciaoNormale: "Ciao! Sono il chatbot AI creato da **Mattia Di Carlo**. Posso aiutarti a spiegare concetti, scrivere testi, creare collegamenti o semplicemente dialogare in modo naturale.",

    ciaoPirandello: "Ciao. In **modalità Pirandello 2.0** posso accompagnarti nel mondo di Luigi Pirandello: la sua vita, le opere, le maschere, la crisi dell'identità e il rapporto tra realtà e finzione."
};

function setPersona(value) {
    persona = value;
    document.body.dataset.persona = value;

    const content = personaContent[value] || personaContent.normale;

    document.querySelector(".mode-icon").innerText = content.icon;
    document.getElementById("modeTitle").innerText = content.title;

    const systemText = value === "pirandello"
        ? "Modalità Pirandello 2.0 attivata: ora il chatbot parlerà soprattutto di Luigi Pirandello, della sua vita, delle sue opere e del tema dell'identità."
        : "Modalità normale attivata: il chatbot risponde come assistente AI quotidiano creato da Mattia Di Carlo.";

    addMessage(systemText, "system");
}

function normalize(text) {
    return String(text || "")
        .toLowerCase()
        .trim()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/[?!.,:;]/g, "")
        .replace(/\s+/g, " ");
}

function isCreatorQuestion(text) {
    const msg = normalize(text);

    return [
        "chi e il tuo creatore",
        "chi ti ha creato",
        "chi ti ha fatto",
        "chi ti ha programmato",
        "chi e il tuo autore",
        "da chi sei stato creato",
        "chi ha creato questo progetto",
        "chi ha creato questa ai",
        "chi e il proprietario"
    ].some(pattern => msg.includes(pattern));
}

function escapeHtml(text) {
    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
}

function formatReply(text) {
    const safeText = escapeHtml(text || "");

    return safeText
        .replace(/^### (.*)$/gm, "<strong class=\"md-heading\">$1</strong>")
        .replace(/^## (.*)$/gm, "<strong class=\"md-heading\">$1</strong>")
        .replace(/^# (.*)$/gm, "<strong class=\"md-heading\">$1</strong>")
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/\n/g, "<br>");
}

function trimHistory() {
    if (conversationHistory.length > MAX_HISTORY_ITEMS) {
        conversationHistory = conversationHistory.slice(-MAX_HISTORY_ITEMS);
    }
}

function remember(role, content) {
    conversationHistory.push({
        role,
        content: String(content || "").slice(0, 1800)
    });

    trimHistory();
}

function addMessage(text, type = "ai") {
    const chat = document.getElementById("chat");
    const message = document.createElement("div");

    message.className = `message ${type}`;
    message.innerHTML = formatReply(text);

    chat.appendChild(message);
    scrollToBottom();

    return message;
}

function addTypingMessage() {
    const chat = document.getElementById("chat");
    const message = document.createElement("div");

    message.className = "message ai typing";
    message.innerHTML = "<span></span><span></span><span></span>";

    chat.appendChild(message);
    scrollToBottom();

    return message;
}

function scrollToBottom() {
    const chat = document.getElementById("chat");
    chat.scrollTop = chat.scrollHeight;
}

function setLoading(value) {
    isSending = value;

    const button = document.getElementById("sendButton");
    const input = document.getElementById("input");

    button.disabled = value;
    input.disabled = value;
}

function usePrompt(text) {
    const input = document.getElementById("input");

    input.value = text;
    resizeTextarea();
    input.focus();

    sendMessage();
}

function resizeTextarea() {
    const input = document.getElementById("input");

    if (!input) return;

    input.style.height = "auto";
    input.style.height = Math.min(input.scrollHeight, 160) + "px";
}

function clearChat() {
    const chat = document.getElementById("chat");

    chat.innerHTML = "";
    conversationHistory = [];

    addMessage(
        "Nuova conversazione avviata. Puoi chiedermi qualcosa in modalità normale oppure attivare Pirandello 2.0 per parlare di vita, opere e identità.",
        "system"
    );

    document.getElementById("input").focus();
}

async function sendMessage() {
    if (isSending) return;

    const input = document.getElementById("input");
    const text = input.value.trim();

    if (!text) return;

    addMessage(text, "user");
    remember("user", text);

    input.value = "";
    resizeTextarea();

    const normalized = normalize(text);

    if (["ciao", "salve", "buongiorno", "buonasera"].includes(normalized)) {
        const reply = persona === "pirandello"
            ? localReplies.ciaoPirandello
            : localReplies.ciaoNormale;

        addMessage(reply, "ai");
        remember("ai", reply);
        return;
    }

    if (isCreatorQuestion(text)) {
        const reply = persona === "pirandello"
            ? localReplies.pirandelloLife
            : localReplies.creator;

        addMessage(reply, "ai");
        remember("ai", reply);
        return;
    }

    const typingMessage = addTypingMessage();

    setLoading(true);

    try {
        const res = await fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: text,
                persona: persona,
                history: conversationHistory.slice(0, -1)
            })
        });

        const data = await res.json();
        const reply = data.reply || "Non ho ricevuto una risposta valida.";

        typingMessage.classList.remove("typing");
        typingMessage.innerHTML = formatReply(reply);

        remember("ai", reply);
    } catch (err) {
        const errorText = "Errore di connessione con il server. Controlla che Flask sia avviato correttamente oppure guarda i log su Render.";

        typingMessage.classList.remove("typing");
        typingMessage.innerHTML = formatReply(errorText);
    } finally {
        setLoading(false);
        input.focus();
        scrollToBottom();
    }
}

document.addEventListener("DOMContentLoaded", () => {
    addMessage(
        "Benvenuto. Sono il chatbot AI creato da **Mattia Di Carlo**. Puoi usarmi per dialogare, chiarire concetti, creare collegamenti o esplorare la modalità **Pirandello 2.0**.",
        "system"
    );

    const input = document.getElementById("input");

    input.addEventListener("input", resizeTextarea);

    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    resizeTextarea();
});
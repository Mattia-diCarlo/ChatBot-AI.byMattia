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
    creator: "Il mio creatore è **Mattia Di Carlo**.\n\nSono stato progettato come parte del suo percorso per l’esame di maturità: non sono soltanto una chat automatica, ma una dimostrazione concreta di come l’intelligenza artificiale possa diventare uno strumento di dialogo, creatività e collegamento tra materie diverse.\n\nMattia ha costruito questo progetto per mostrare che la tecnologia non è solo codice: può diventare una voce digitale capace di spiegare, argomentare, cambiare prospettiva e accompagnare chi ascolta dentro un ragionamento.",
    ciao: "Ciao! Sono il chatbot AI creato da **Mattia Di Carlo**. Posso aiutarti a spiegare il progetto, ragionare sull’intelligenza artificiale oppure entrare nella modalità **Pirandello 2.0**, dove tecnologia e identità diventano un vero dialogo da presentazione d’esame."
};

function setPersona(value) {
    persona = value;
    document.body.dataset.persona = value;

    const content = personaContent[value] || personaContent.normale;

    document.querySelector(".mode-icon").innerText = content.icon;
    document.getElementById("modeTitle").innerText = content.title;

    const systemText = value === "pirandello"
        ? "Modalità Pirandello 2.0 attivata: ora il chatbot risponderà in modo più discorsivo, teatrale e collegato al tema dell'identità."
        : "Modalità normale attivata: risposte chiare, moderne e adatte alla presentazione del progetto.";

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
        "Nuova conversazione avviata. Sono pronto: puoi chiedermi di spiegare il progetto, l’intelligenza artificiale o la modalità Pirandello 2.0.",
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
        addMessage(localReplies.ciao, "ai");
        remember("ai", localReplies.ciao);
        return;
    }

    if (isCreatorQuestion(text)) {
        addMessage(localReplies.creator, "ai");
        remember("ai", localReplies.creator);
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
        "Benvenuto. Sono il chatbot AI creato da **Mattia Di Carlo**: posso spiegare il progetto, collegare l’intelligenza artificiale alle materie d’esame e trasformare Pirandello in un dialogo moderno sull’identità.",
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

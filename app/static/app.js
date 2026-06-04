const tokenInput = document.querySelector("#tokenInput");
const saveTokenButton = document.querySelector("#saveTokenButton");
const statusEl = document.querySelector("#status");
const chatLog = document.querySelector("#chatLog");
const chatForm = document.querySelector("#chatForm");
const messageInput = document.querySelector("#messageInput");
const micButton = document.querySelector("#micButton");
const resetButton = document.querySelector("#resetButton");
const spotifyButton = document.querySelector("#spotifyButton");
const confirmPanel = document.querySelector("#confirmPanel");
const confirmText = document.querySelector("#confirmText");
const approveButton = document.querySelector("#approveButton");
const denyButton = document.querySelector("#denyButton");

let authToken = localStorage.getItem("jarvisToken") || "";
let recorder = null;
let chunks = [];
let pendingConfirmationId = null;

tokenInput.value = authToken;
setStatus(authToken ? "Paired. Ready." : "Paste your pairing token to connect.");

saveTokenButton.addEventListener("click", () => {
  authToken = tokenInput.value.trim();
  localStorage.setItem("jarvisToken", authToken);
  setStatus("Paired. Ready.");
});

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = messageInput.value.trim();
  if (!message) return;
  messageInput.value = "";
  addMessage("user", message);
  await sendChat(message);
});

resetButton.addEventListener("click", async () => {
  if (!confirm("Reset encrypted JARVIS memory?")) return;
  await api("/api/memory/reset", { method: "POST" });
  addMessage("system", "Memory reset.");
});

spotifyButton.addEventListener("click", async () => {
  const data = await api("/api/spotify/login");
  window.open(data.url, "_blank", "noopener");
});

approveButton.addEventListener("click", async () => {
  await confirmTool(true);
});

denyButton.addEventListener("click", async () => {
  await confirmTool(false);
});

micButton.addEventListener("click", async () => {
  if (recorder && recorder.state === "recording") {
    recorder.stop();
    micButton.textContent = "Mic";
    return;
  }
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  chunks = [];
  recorder = new MediaRecorder(stream);
  recorder.ondataavailable = (event) => chunks.push(event.data);
  recorder.onstop = async () => {
    stream.getTracks().forEach((track) => track.stop());
    const blob = new Blob(chunks, { type: "audio/webm" });
    const form = new FormData();
    form.append("file", blob, "speech.webm");
    const data = await api("/api/voice/transcribe", { method: "POST", body: form, skipContentType: true });
    messageInput.value = data.transcript;
    if (data.transcript) {
      addMessage("user", data.transcript);
      await sendChat(data.transcript, true);
    }
  };
  recorder.start();
  micButton.textContent = "Stop";
});

async function sendChat(message, speak = false) {
  setBusy(true);
  try {
    const data = await api("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message }),
    });
    addMessage("assistant", data.reply);
    handleToolResults(data.tool_results || []);
    if (speak) await playTts(data.reply);
  } finally {
    setBusy(false);
  }
}

function handleToolResults(results) {
  const pending = results.find((result) => result.requires_confirmation);
  if (!pending) return;
  pendingConfirmationId = pending.confirmation_id;
  confirmText.textContent = `Approve ${pending.tool}? ${JSON.stringify(pending.result?.args || {})}`;
  confirmPanel.classList.remove("hidden");
}

async function confirmTool(approve) {
  if (!pendingConfirmationId) return;
  const data = await api("/api/tools/confirm", {
    method: "POST",
    body: JSON.stringify({ confirmation_id: pendingConfirmationId, approve }),
  });
  confirmPanel.classList.add("hidden");
  pendingConfirmationId = null;
  addMessage("system", data.ok ? `${data.tool} completed.` : `${data.tool} denied or failed: ${data.error}`);
}

async function playTts(text) {
  const response = await fetch("/api/voice/tts", {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify({ text }),
  });
  if (!response.ok) throw new Error(await response.text());
  const blob = await response.blob();
  const audio = new Audio(URL.createObjectURL(blob));
  await audio.play();
}

async function api(path, options = {}) {
  if (!authToken) throw new Error("Missing pairing token");
  const headers = options.skipContentType ? { Authorization: `Bearer ${authToken}` } : jsonHeaders();
  const response = await fetch(path, { ...options, headers });
  if (!response.ok) {
    const text = await response.text();
    addMessage("system", text);
    throw new Error(text);
  }
  return response.json();
}

function jsonHeaders() {
  return {
    Authorization: `Bearer ${authToken}`,
    "Content-Type": "application/json",
  };
}

function addMessage(role, text) {
  const el = document.createElement("div");
  el.className = `message ${role}`;
  el.textContent = text;
  chatLog.appendChild(el);
  chatLog.scrollTop = chatLog.scrollHeight;
}

function setStatus(text) {
  statusEl.textContent = text;
}

function setBusy(busy) {
  chatForm.querySelectorAll("button, input").forEach((el) => {
    el.disabled = busy;
  });
}


const BASE_URL = "http://127.0.0.1:5000";
const dismissedSuggestions = new Set();

async function loadDrafts() {
  const el = document.getElementById("drafts");
  const [data, scheduledData] = await Promise.all([
    fetch(`${BASE_URL}/pending-drafts`).then(r => r.json()),
    fetch(`${BASE_URL}/scheduled`).then(r => r.json())
  ]);

  const scheduledIds = new Set(scheduledData.map(s => s.draft_id));
  const trulyPending = data.filter(d => !scheduledIds.has(d.draft_id));

  if (trulyPending.length === 0) {
    el.innerHTML = "<p class='empty'>Nothing here right now.</p>";
    return;
  }

  el.innerHTML = trulyPending.map((d, i) => `
    <div class="item">
      <span class="tag ${d.type}">${d.type}</span>
      <b>${d.subject}</b><br>
      <small>${d.sender}</small>
      <div class="reply-preview">
        <span class="preview-label">Draft reply:</span>
        <p class="preview-text">${d.reply_text || "(no preview available)"}</p>
      </div>
      <div class="schedule-row">
        <input type="number" min="0" value="180" class="delay-input" data-index="${i}">
        <span class="unit">min</span>
        <button class="schedule-btn" data-index="${i}">Schedule Send</button>
      </div>
    </div>
  `).join("");

  document.querySelectorAll(".schedule-btn").forEach(btn => {
    btn.addEventListener("click", async () => {
      const i = btn.dataset.index;
      const d = trulyPending[i];
      const delay = document.querySelector(`.delay-input[data-index="${i}"]`).value;
      btn.disabled = true;
      btn.textContent = "Scheduling...";
      try {
        const res = await fetch(`${BASE_URL}/schedule`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ draft_id: d.draft_id, subject: d.subject, delay_minutes: parseInt(delay) })
        });
        if (!res.ok) {
          btn.textContent = "Failed ✗";
          return;
        }
        loadDrafts();
        loadScheduled();
      } catch (e) {
        btn.textContent = "Error - see console";
      }
    });
  });
}

async function loadScheduled() {
  const el = document.getElementById("scheduled");
  const data = await fetch(`${BASE_URL}/scheduled`).then(r => r.json());

  if (data.length === 0) {
    el.innerHTML = "<p class='empty'>Nothing here right now.</p>";
    return;
  }

  el.innerHTML = data.map((s, i) => `
    <div class="item">
      <b>${s.subject}</b><br>
      <small>sends at ${new Date(s.send_at).toLocaleString()}</small><br>
      <button class="cancel-btn" data-index="${i}">Cancel</button>
    </div>
  `).join("");

  document.querySelectorAll(".cancel-btn").forEach(btn => {
    btn.addEventListener("click", async () => {
      const s = data[btn.dataset.index];
      btn.disabled = true;
      btn.textContent = "Cancelling...";
      await fetch(`${BASE_URL}/cancel-scheduled`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ draft_id: s.draft_id })
      });
      loadDrafts();
      loadScheduled();
    });
  });
}

function looksLikeCode(text) {
  const codeSignals = [
    "font-family", "font-size", "color:", "background", "padding",
    "margin", "width:", "height:", "display:", "position:",
    "{", "}", "!important", "@media", "px;", "em;"
  ];
  return codeSignals.some(signal => text.toLowerCase().includes(signal));
}

function isGoodSuggestion(s) {
  if (!s.question || s.question.trim().length < 10) return false;
  if (s.question.trim().length > 200) return false;
  if (looksLikeCode(s.question)) return false;
  if (dismissedSuggestions.has(s.question)) return false;
  return true;
}

async function loadSuggestions() {
  const el = document.getElementById("suggestions");
  const data = await fetch(`${BASE_URL}/suggestions`).then(r => r.json());
  const cleanData = data.filter(isGoodSuggestion);

  if (cleanData.length === 0) {
    el.innerHTML = "<p class='empty'>Nothing here right now.</p>";
    return;
  }

  el.innerHTML = cleanData.map((s, i) => `
    <div class="item" id="suggestion-${i}">
      <b>${s.question}</b><br>
      <small class="suggest-meta">seen ${s.count} times</small>
      <div class="suggest-reply">
        <span class="suggest-label">Suggested reply:</span>
        ${s.reply}
      </div>
      <button class="accept-btn" data-index="${i}">Accept as template</button>
      <button class="dismiss-btn" data-index="${i}">Dismiss</button>
    </div>
  `).join("");

  document.querySelectorAll(".accept-btn").forEach(btn => {
    btn.addEventListener("click", async () => {
      const s = cleanData[btn.dataset.index];
      btn.disabled = true;
      btn.textContent = "Adding...";
      await fetch(`${BASE_URL}/templates`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: s.question, reply: s.reply })
      });
      btn.textContent = "Added ✓";
      dismissedSuggestions.add(s.question);
      document.getElementById(`suggestion-${btn.dataset.index}`).style.opacity = "0.5";
    });
  });

  document.querySelectorAll(".dismiss-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      const s = cleanData[btn.dataset.index];
      dismissedSuggestions.add(s.question);
      document.getElementById(`suggestion-${btn.dataset.index}`).style.display = "none";
    });
  });
}

async function loadMode() {
  const btn = document.getElementById("mode-btn");
  try {
    const res = await fetch(`${BASE_URL}/mode`);
    const data = await res.json();
    renderModeBtn(btn, data.mode);
  } catch (e) {
    btn.textContent = "Unknown";
  }
}

function renderModeBtn(btn, currentMode) {
  if (currentMode === "automated") {
    btn.textContent = "Fully Automated";
    btn.className = "mode-btn automated";
  } else {
    btn.textContent = "Hybrid";
    btn.className = "mode-btn hybrid";
  }

  btn.onclick = async () => {
    const newMode = currentMode === "automated" ? "hybrid" : "automated";
    const res = await fetch(`${BASE_URL}/mode`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: newMode })
    });
    if (res.ok) {
      currentMode = newMode;
      renderModeBtn(btn, newMode);
      loadDrafts();
    }
  };
}

loadDrafts();
loadScheduled();
loadSuggestions();
loadMode();
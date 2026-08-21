const BASE_URL = "http://127.0.0.1:5000";

async function loadSummary() {
  const el = document.getElementById("summary");
  try {
    const [drafts, scheduled, suggestions] = await Promise.all([
      fetch(`${BASE_URL}/pending-drafts`).then(r => r.json()),
      fetch(`${BASE_URL}/scheduled`).then(r => r.json()),
      fetch(`${BASE_URL}/suggestions`).then(r => r.json())
    ]);

    el.innerHTML = `
      <div class="stat"><b>${drafts.length}</b><span>Drafts pending review</span></div>
      <div class="stat"><b>${scheduled.length}</b><span>Scheduled to send</span></div>
      <div class="stat"><b>${suggestions.length}</b><span>New template suggestions</span></div>
    `;
  } catch (e) {
    el.innerHTML = "<p class='error'>Can't reach the server. Is app.py running?</p>";
  }
}

document.getElementById("openDashboard").addEventListener("click", () => {
  chrome.tabs.create({ url: chrome.runtime.getURL("dashboard.html") });
});

loadSummary();
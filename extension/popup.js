const API = "https://api.gotot.app";
const urlInput = document.getElementById("urlInput");
const analyzeBtn = document.getElementById("analyzeBtn");
const infoPanel = document.getElementById("infoPanel");
const videoTitle = document.getElementById("videoTitle");
const videoMeta = document.getElementById("videoMeta");
const formatList = document.getElementById("formatList");
const errorMsg = document.getElementById("errorMsg");

analyzeBtn.addEventListener("click", async () => {
  const url = urlInput.value.trim();
  if (!url) { showError("Please enter a URL"); return; }
  hideError();
  analyzeBtn.disabled = true;
  analyzeBtn.textContent = "Analyzing...";

  try {
    const resp = await fetch(`${API}/download/info`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    if (!resp.ok) { showError("Failed to analyze video"); return; }
    const data = await resp.json();
    showInfo(data, url);
  } catch (e) {
    showError("Network error. Check your connection.");
  } finally {
    analyzeBtn.disabled = false;
    analyzeBtn.textContent = "Analyze & Download";
  }
});

function showInfo(data, url) {
  videoTitle.textContent = data.title || "Untitled";
  videoMeta.textContent = `${data.platform} • ${formatDuration(data.duration)}`;
  formatList.innerHTML = "";

  const formats = data.formats || [];
  const shown = formats.slice(0, 8);
  shown.forEach((f) => {
    const div = document.createElement("div");
    div.className = "format-item";
    const label = f.resolution || f.format_id;
    div.innerHTML = `
      <span style="font-size:12px;">${label} (${f.ext.toUpperCase()})</span>
      <button onclick="startDownload('${url}', '${f.format_id}')">Download</button>
    `;
    formatList.appendChild(div);
  });

  infoPanel.classList.add("show");
}

async function startDownload(url, formatId) {
  try {
    const resp = await fetch(`${API}/download/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, format_id: formatId }),
    });
    const data = await resp.json();
    if (data.download_url) {
      window.open(`${API}${data.download_url}`, "_blank");
    }
  } catch (e) {
    showError("Download failed");
  }
}

function formatDuration(s) {
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  if (h > 0) return `${h}:${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
  return `${m}:${String(sec).padStart(2, "0")}`;
}

function showError(msg) {
  errorMsg.textContent = msg;
  errorMsg.classList.add("show");
  infoPanel.classList.remove("show");
}

function hideError() {
  errorMsg.classList.remove("show");
}

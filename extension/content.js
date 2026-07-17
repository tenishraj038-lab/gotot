(() => {
  const GOTOT_URL = "https://gotot.app";

  const injectButton = () => {
    const existing = document.getElementById("gotot-download-btn");
    if (existing) return;

    const btn = document.createElement("div");
    btn.id = "gotot-download-btn";
    btn.innerHTML = `
      <div style="
        position: fixed; bottom: 24px; right: 24px; z-index: 999999;
        background: linear-gradient(135deg, #3b82f6, #c026d3);
        color: white; border: none; border-radius: 16px;
        padding: 12px 20px; font-size: 14px; font-weight: 600;
        cursor: pointer; box-shadow: 0 8px 32px rgba(59,130,246,0.3);
        display: flex; align-items: center; gap: 8px;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        transition: transform 0.2s, box-shadow 0.2s;
      ">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
          <polyline points="7 10 12 15 17 10"/>
          <line x1="12" y1="15" x2="12" y2="3"/>
        </svg>
        Download with GoTot
      </div>
    `;

    btn.addEventListener("mouseenter", () => {
      const el = btn.querySelector("div");
      if (el) { el.style.transform = "scale(1.05)"; el.style.boxShadow = "0 12px 40px rgba(59,130,246,0.4)"; }
    });
    btn.addEventListener("mouseleave", () => {
      const el = btn.querySelector("div");
      if (el) { el.style.transform = "scale(1)"; el.style.boxShadow = "0 8px 32px rgba(59,130,246,0.3)"; }
    });

    btn.addEventListener("click", () => {
      window.open(GOTOT_URL, "_blank");
    });

    document.body.appendChild(btn);
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", injectButton);
  } else {
    injectButton();
  }
})();

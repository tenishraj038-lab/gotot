const GOTOT_API = "https://api.gotot.app";

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "DOWNLOAD_VIDEO") {
    handleDownload(message.url, message.formatId).then(sendResponse);
    return true;
  }
  if (message.type === "GET_VIDEO_INFO") {
    getVideoInfo(message.url).then(sendResponse);
    return true;
  }
});

async function getVideoInfo(url) {
  try {
    const resp = await fetch(`${GOTOT_API}/download/info`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });
    return await resp.json();
  } catch (e) {
    return { error: e.message };
  }
}

async function handleDownload(url, formatId) {
  try {
    const resp = await fetch(`${GOTOT_API}/download/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, format_id: formatId }),
    });
    const data = await resp.json();
    if (data.download_url) {
      chrome.downloads.download({ url: `${GOTOT_API}${data.download_url}`, filename: data.file_name + "." + data.format });
    }
    return data;
  } catch (e) {
    return { error: e.message };
  }
}

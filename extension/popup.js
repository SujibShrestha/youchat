const API_URL = "http://localhost:8000";

const form = document.getElementById("question-form");
const questionInput = document.getElementById("question");
const askButton = document.getElementById("ask-button");
const answerOutput = document.getElementById("answer");
const statusOutput = document.getElementById("status");

function getVideoIdFromUrl(url) {
  let parsedUrl;

  try {
    parsedUrl = new URL(url);
  } catch {
    return null;
  }

  if (parsedUrl.hostname.includes("youtu.be")) {
    return parsedUrl.pathname.split("/").filter(Boolean)[0] || null;
  }

  if (!parsedUrl.hostname.includes("youtube.com")) {
    return null;
  }

  if (parsedUrl.pathname === "/watch") {
    return parsedUrl.searchParams.get("v");
  }

  const pathParts = parsedUrl.pathname.split("/").filter(Boolean);
  if (pathParts[0] === "shorts" || pathParts[0] === "embed" || pathParts[0] === "live") {
    return pathParts[1] || null;
  }

  return null;
}

async function getPageUrl(tabId) {
  const results = await chrome.scripting.executeScript({
    target: { tabId },
    func: () => window.location.href
  });

  return results[0]?.result || null;
}

async function getCurrentVideoId() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  const currentTab = tabs[0];

  if (!currentTab) {
    return null;
  }

  const tabVideoId = getVideoIdFromUrl(currentTab.url);
  if (tabVideoId) {
    return tabVideoId;
  }

  try {
    const pageUrl = await getPageUrl(currentTab.id);
    return getVideoIdFromUrl(pageUrl);
  } catch {
    return null;
  }
}

async function loadLatestAnswer() {
  try {
    const response = await fetch(`${API_URL}/answer`);
    const data = await response.json();
    statusOutput.textContent = "API connected";

    if (data.answer) {
      answerOutput.textContent = data.answer;
      questionInput.value = data.question || "";
    }
  } catch {
    statusOutput.textContent = "API offline";
    answerOutput.textContent = "Start the FastAPI server first.";
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const question = questionInput.value.trim();
  if (!question) {
    answerOutput.textContent = "Enter a question first.";
    return;
  }

  askButton.disabled = true;
  askButton.textContent = "Asking...";
  statusOutput.textContent = "Working";
  answerOutput.textContent = "Thinking...";

  try {
    const videoId = await getCurrentVideoId();
    if (!videoId) {
      statusOutput.textContent = "No video detected";
      answerOutput.textContent = "Open a YouTube video tab, then click the extension again.";
      return;
    }

    const response = await fetch(`${API_URL}/question`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ question, video_id: videoId })
    });

    const data = await response.json();

    if (!response.ok) {
      statusOutput.textContent = "Request failed";
      answerOutput.textContent = data.detail || "Request failed.";
      return;
    }

    statusOutput.textContent = `Video ${videoId}`;
    answerOutput.textContent = data.answer || "No answer returned.";
  } catch {
    statusOutput.textContent = "API offline";
    answerOutput.textContent = "Could not connect to the FastAPI server.";
  } finally {
    askButton.disabled = false;
    askButton.textContent = "Ask";
  }
});

loadLatestAnswer();

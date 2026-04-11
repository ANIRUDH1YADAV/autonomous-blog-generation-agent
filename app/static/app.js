const form = document.getElementById("blog-form");
const topicInput = document.getElementById("topic");
const targetLanguageInput = document.getElementById("target-language");
const generateButton = document.getElementById("generate-btn");
const statusEl = document.getElementById("status");

const resultSection = document.getElementById("result");
const blogTitleEl = document.getElementById("blog-title");
const blogContentEl = document.getElementById("blog-content");
const imagesWrapEl = document.getElementById("images-wrap");
const imagesGridEl = document.getElementById("images-grid");
const progressWrapEl = document.getElementById("progress-wrap");
const progressListEl = document.getElementById("progress-list");
const textStatsEl = document.getElementById("text-stats");
const statsToggleEl = document.getElementById("stats-toggle");
const statsMenuEl = document.getElementById("stats-menu");
const statWordsEl = document.getElementById("stat-words");
const statCharactersEl = document.getElementById("stat-characters");
const statSentencesEl = document.getElementById("stat-sentences");
const statParagraphsEl = document.getElementById("stat-paragraphs");
const statReadTimeEl = document.getElementById("stat-read-time");

let seenStages = new Set();
let blogMarkdownBuffer = "";
let renderQueued = false;

function setStatus(message, type = "") {
  statusEl.textContent = message;
  statusEl.classList.remove("error", "success");
  if (type) {
    statusEl.classList.add(type);
  }
}

function normalizeImagePath(pathValue) {
  if (!pathValue) {
    return "";
  }

  const normalized = String(pathValue).replaceAll("\\", "/").replace(/^\.?\//, "");

  if (normalized.startsWith("generated_images/")) {
    return `/${normalized}`;
  }

  return `/generated_images/${normalized.split("/").pop()}`;
}

function renderImages(images) {
  imagesGridEl.innerHTML = "";

  if (!Array.isArray(images) || images.length === 0) {
    imagesWrapEl.classList.add("hidden");
    return;
  }

  images.forEach((item) => {
    const figure = document.createElement("figure");
    figure.className = "image-card";

    const img = document.createElement("img");
    img.src = normalizeImagePath(item.path);
    img.alt = item.alt || item.section || "Generated diagram";

    const caption = document.createElement("figcaption");
    caption.textContent = item.section || "Generated diagram";

    figure.appendChild(img);
    figure.appendChild(caption);
    imagesGridEl.appendChild(figure);
  });

  imagesWrapEl.classList.remove("hidden");
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString();
}

function computeStats(text) {
  const raw = String(text || "");
  const compact = raw.trim();

  const words = compact ? compact.split(/\s+/).filter(Boolean).length : 0;
  const characters = raw.length;
  const sentences = compact ? (compact.match(/[^.!?]+[.!?]+(?=\s|$)|[^.!?]+$/g) || []).length : 0;

  const paragraphs = compact
    ? compact
        .split(/\n\s*\n+/)
        .map((chunk) => chunk.trim())
        .filter(Boolean).length
    : 0;

  const readMinutes = words > 0 ? Math.max(1, Math.ceil(words / 200)) : 0;

  return {
    words,
    characters,
    sentences,
    paragraphs,
    readMinutes,
  };
}

function closeStatsMenu() {
  statsMenuEl.classList.add("hidden");
  statsToggleEl.setAttribute("aria-expanded", "false");
}

function updateTextStats(renderedText) {
  const stats = computeStats(renderedText);

  if (stats.words === 0) {
    textStatsEl.classList.add("hidden");
    closeStatsMenu();
    return;
  }

  textStatsEl.classList.remove("hidden");

  statsToggleEl.innerHTML = `${formatNumber(stats.words)} words <span class="caret" aria-hidden="true">▾</span>`;
  statWordsEl.innerHTML = `<span>${formatNumber(stats.words)} words</span><span class="check" aria-hidden="true">✓</span>`;
  statCharactersEl.textContent = `${formatNumber(stats.characters)} characters`;
  statSentencesEl.textContent = `${formatNumber(stats.sentences)} sentences`;
  statParagraphsEl.textContent = `${formatNumber(stats.paragraphs)} paragraphs`;
  statReadTimeEl.textContent = `${formatNumber(stats.readMinutes)} min read`;
}

function renderBlogMarkdown(markdownText) {
  if (window.marked) {
    const html = window.marked.parse(markdownText || "", {
      gfm: true,
      breaks: true,
    });

    if (window.DOMPurify) {
      blogContentEl.innerHTML = window.DOMPurify.sanitize(html);
      updateTextStats(blogContentEl.textContent);
      return;
    }

    blogContentEl.innerHTML = html;
    updateTextStats(blogContentEl.textContent);
    return;
  }

  // Fallback when parser scripts are unavailable.
  blogContentEl.textContent = markdownText || "";
  updateTextStats(blogContentEl.textContent);
}

function scheduleBlogRender() {
  if (renderQueued) {
    return;
  }

  renderQueued = true;

  window.requestAnimationFrame(() => {
    renderQueued = false;
    renderBlogMarkdown(blogMarkdownBuffer);
  });
}

function resetProgress() {
  seenStages = new Set();
  progressListEl.innerHTML = "";
  progressWrapEl.classList.add("hidden");
}

function addProgressStep(stage, message) {
  if (!stage || seenStages.has(stage)) {
    return;
  }

  seenStages.add(stage);

  const item = document.createElement("li");
  item.textContent = message || stage;
  progressListEl.appendChild(item);
  progressWrapEl.classList.remove("hidden");
}

function resetResultArea() {
  blogTitleEl.textContent = "";
  blogMarkdownBuffer = "";
  renderBlogMarkdown(blogMarkdownBuffer);
  textStatsEl.classList.add("hidden");
  closeStatsMenu();
  renderImages([]);
  resultSection.classList.remove("hidden");
}

function parseEventBlock(block) {
  const lines = block.split("\n");
  let eventName = "message";
  const dataLines = [];

  for (const line of lines) {
    if (line.startsWith("event:")) {
      eventName = line.slice(6).trim();
      continue;
    }

    if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trimStart());
    }
  }

  if (dataLines.length === 0) {
    return null;
  }

  const dataText = dataLines.join("\n");

  try {
    return { eventName, payload: JSON.parse(dataText) };
  } catch {
    return { eventName, payload: { message: dataText } };
  }
}

async function consumeEventStream(response, onEvent) {
  if (!response.body) {
    throw new Error("Streaming is not supported by this browser.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });

    while (true) {
      const splitIndex = buffer.indexOf("\n\n");
      if (splitIndex === -1) {
        break;
      }

      const block = buffer.slice(0, splitIndex);
      buffer = buffer.slice(splitIndex + 2);

      const parsed = parseEventBlock(block);
      if (!parsed) {
        continue;
      }

      onEvent(parsed.eventName, parsed.payload);
    }
  }
}

statsToggleEl.addEventListener("click", () => {
  const isHidden = statsMenuEl.classList.contains("hidden");
  if (isHidden) {
    statsMenuEl.classList.remove("hidden");
    statsToggleEl.setAttribute("aria-expanded", "true");
    return;
  }

  closeStatsMenu();
});

document.addEventListener("click", (event) => {
  if (textStatsEl.classList.contains("hidden")) {
    return;
  }

  if (!textStatsEl.contains(event.target)) {
    closeStatsMenu();
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const topic = topicInput.value.trim();
  const targetLanguage = targetLanguageInput.value;

  if (!topic) {
    setStatus("Please enter a topic.", "error");
    return;
  }

  resetProgress();
  resetResultArea();
  setStatus("Starting workflow...");
  generateButton.disabled = true;

  try {
    const response = await fetch("/api/v1/generate_blog/stream", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        topic,
        target_language: targetLanguage,
      }),
    });

    if (!response.ok) {
      let message = "Generation failed.";
      try {
        const errorData = await response.json();
        message = errorData.detail || message;
      } catch {
        // Keep default message when response is not JSON.
      }
      throw new Error(message);
    }

    let streamCompleted = false;

    await consumeEventStream(response, (eventName, payload) => {
      if (eventName === "progress") {
        setStatus(payload.message || "Working...");
        addProgressStep(payload.stage, payload.message);
        return;
      }

      if (eventName === "title") {
        blogTitleEl.textContent = payload.title || "Generated Blog";
        return;
      }

      if (eventName === "word" || eventName === "line") {
        blogMarkdownBuffer += payload.text || "";
        scheduleBlogRender();
        return;
      }

      if (eventName === "images") {
        renderImages(payload.images || []);
        return;
      }

      if (eventName === "done") {
        streamCompleted = true;
        renderBlogMarkdown(blogMarkdownBuffer);
        blogTitleEl.textContent = payload.title || blogTitleEl.textContent || "Generated Blog";
        renderImages(payload.images || []);
        setStatus("Blog generated successfully.", "success");
        return;
      }

      if (eventName === "error") {
        throw new Error(payload.message || "Streaming generation failed.");
      }
    });

    if (!streamCompleted) {
      throw new Error("Generation stream ended before completion.");
    }

    resultSection.scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    setStatus(error.message || "Failed to generate blog.", "error");
  } finally {
    generateButton.disabled = false;
  }
});

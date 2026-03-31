const state = {
  config: null,
  status: null,
};

const elements = {};

document.addEventListener("DOMContentLoaded", async () => {
  cacheElements();
  wireEvents();
  await loadConfig();
  await Promise.all([loadStatus(), loadLibrary()]);
});

function cacheElements() {
  elements.form = document.getElementById("generatorForm");
  elements.prompt = document.getElementById("prompt");
  elements.provider = document.getElementById("provider");
  elements.model = document.getElementById("model");
  elements.host = document.getElementById("llm_host");
  elements.temperature = document.getElementById("llm_temperature");
  elements.seed = document.getElementById("seed");
  elements.sampleRate = document.getElementById("sample_rate");
  elements.immersion = document.getElementById("immersion");
  elements.ambienceOptions = document.getElementById("ambienceOptions");
  elements.exportStems = document.getElementById("export_stems");
  elements.generateButton = document.getElementById("generateButton");
  elements.submitStatus = document.getElementById("submitStatus");
  elements.resultPanel = document.getElementById("resultPanel");
  elements.libraryList = document.getElementById("libraryList");
  elements.statusPill = document.getElementById("statusPill");
  elements.statusMeta = document.getElementById("statusMeta");
  elements.libraryCount = document.getElementById("libraryCount");
  elements.outputDir = document.getElementById("outputDir");
  elements.refreshLibrary = document.getElementById("refreshLibrary");
}

function wireEvents() {
  elements.form.addEventListener("submit", onSubmit);
  elements.provider.addEventListener("change", syncProviderFields);
  elements.refreshLibrary.addEventListener("click", loadLibrary);
  document.querySelectorAll(".prompt-chip").forEach((button) => {
    button.addEventListener("click", () => {
      elements.prompt.value = button.dataset.prompt || "";
      elements.prompt.focus();
    });
  });
}

async function loadConfig() {
  const response = await fetch("/api/config");
  const config = await response.json();
  state.config = config;

  populateSelect(elements.provider, config.providers, config.defaults.provider);
  populateSelect(elements.immersion, ["", ...config.immersion_modes], "");
  elements.model.value = config.defaults.model;
  elements.host.value = config.defaults.llm_host;
  elements.sampleRate.value = config.defaults.sample_rate;
  renderAmbienceOptions(config.ambience_layers);
  syncProviderFields();
}

async function loadStatus() {
  try {
    const host = encodeURIComponent(elements.host.value || "http://127.0.0.1:11434");
    const response = await fetch(`/api/status?host=${host}`);
    const payload = await response.json();
    state.status = payload;
    elements.libraryCount.textContent = `${payload.library_count} tracks`;
    elements.outputDir.textContent = payload.output_dir;

    if (payload.ollama.reachable) {
      elements.statusPill.className = "status-pill ok";
      elements.statusPill.textContent = "Local LLM ready";
      const models = payload.ollama.models.slice(0, 4).join(", ");
      elements.statusMeta.textContent = models
        ? `Ollama is reachable at ${payload.ollama.host}. Models: ${models}`
        : `Ollama is reachable at ${payload.ollama.host}.`;
    } else {
      elements.statusPill.className = "status-pill warn";
      elements.statusPill.textContent = "LLM offline or unavailable";
      elements.statusMeta.textContent = payload.ollama.error || `Could not reach ${payload.ollama.host}`;
    }
  } catch (error) {
    elements.statusPill.className = "status-pill warn";
    elements.statusPill.textContent = "Status check failed";
    elements.statusMeta.textContent = String(error);
  }
}

async function loadLibrary() {
  elements.libraryList.innerHTML = `<div class="empty-state">Loading recent tracks…</div>`;
  try {
    const response = await fetch("/api/library?limit=18");
    const payload = await response.json();
    renderLibrary(payload.items || []);
  } catch (error) {
    elements.libraryList.innerHTML = `<div class="empty-state">Could not load recent tracks: ${escapeHtml(String(error))}</div>`;
  }
}

function populateSelect(select, values, selectedValue) {
  select.innerHTML = "";
  values.forEach((value) => {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value === "" ? "auto" : value;
    if (value === selectedValue) {
      option.selected = true;
    }
    select.appendChild(option);
  });
}

function renderAmbienceOptions(layers) {
  elements.ambienceOptions.innerHTML = "";
  layers.forEach((layer) => {
    const label = document.createElement("label");
    label.className = "ambience-chip";

    const input = document.createElement("input");
    input.type = "checkbox";
    input.name = "ambience";
    input.value = layer;

    const span = document.createElement("span");
    span.textContent = layer;

    label.appendChild(input);
    label.appendChild(span);
    elements.ambienceOptions.appendChild(label);
  });
}

function syncProviderFields() {
  const fallback = elements.provider.value === "fallback";
  elements.model.disabled = fallback;
  elements.host.disabled = fallback;
  elements.temperature.disabled = fallback;
}

async function onSubmit(event) {
  event.preventDefault();
  const payload = collectPayload();
  setSubmitting(true, "Generating with the Python engine…");

  try {
    const response = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const message = await response.text();
      throw new Error(message || `Request failed with ${response.status}`);
    }

    const data = await response.json();
    renderResult(data.result);
    renderLibrary(data.library || []);
    await loadStatus();
    setSubmitting(false, "Track generated.");
  } catch (error) {
    setSubmitting(false, `Generation failed: ${String(error)}`);
  }
}

function collectPayload() {
  return {
    prompt: elements.prompt.value.trim(),
    provider: elements.provider.value,
    model: elements.model.value.trim(),
    llm_host: elements.host.value.trim(),
    llm_temperature: Number(elements.temperature.value || "0.95"),
    seed: elements.seed.value ? Number(elements.seed.value) : null,
    sample_rate: Number(elements.sampleRate.value || "44100"),
    immersion: elements.immersion.value || null,
    ambience: Array.from(document.querySelectorAll('input[name="ambience"]:checked')).map((node) => node.value),
    export_stems: elements.exportStems.checked,
  };
}

function setSubmitting(active, message) {
  elements.generateButton.disabled = active;
  elements.generateButton.textContent = active ? "Generating…" : "Generate Track";
  elements.submitStatus.textContent = message;
}

function renderResult(result) {
  const plan = result.metadata.plan;
  const render = result.metadata.render;
  const composition = result.metadata.composition;
  const stemLinks = (result.stem_urls || [])
    .map((url) => `<a href="${url}" target="_blank" rel="noreferrer">${escapeHtml(fileName(url))}</a>`)
    .join("");

  elements.resultPanel.className = "result-panel";
  elements.resultPanel.innerHTML = `
    <div class="result-top">
      <article class="result-summary">
        <p class="label">Now Playing</p>
        <h2>${escapeHtml(plan.title)}</h2>
        <p>${escapeHtml(plan.description)}</p>
      </article>
      <div class="meta-grid">
        <div class="meta-block">
          <strong>Core</strong>
          <div class="meta-line">${escapeHtml(plan.key)} ${escapeHtml(plan.mode)} · ${escapeHtml(String(plan.bpm))} BPM</div>
          <div class="meta-line">${escapeHtml(plan.progression_family)} · ${escapeHtml(plan.drum_style)}</div>
        </div>
        <div class="meta-block">
          <strong>World</strong>
          <div class="meta-line">${escapeHtml(plan.immersion_mode)}</div>
          <div class="meta-line">${escapeHtml((plan.ambience_layers || []).join(", ") || "none")}</div>
        </div>
        <div class="meta-block">
          <strong>Palette</strong>
          <div class="meta-line">${escapeHtml(plan.keys_sound)} · ${escapeHtml(plan.bass_sound)} · ${escapeHtml(plan.lead_sound)}</div>
          <div class="meta-line">${escapeHtml(plan.counter_sound)} · ${escapeHtml(plan.percussion_style)}</div>
        </div>
        <div class="meta-block">
          <strong>Riffs</strong>
          <div class="meta-line">${escapeHtml(plan.riff_shape)} · ${escapeHtml(plan.motif_variation)}</div>
          <div class="meta-line">density ${escapeHtml(String(plan.riff_density))} · variety ${escapeHtml(String(plan.variety_amount))}</div>
        </div>
      </div>
    </div>
    <article class="track-card">
      <strong>Preview</strong>
      <audio controls preload="none" src="${result.wav_url}"></audio>
      <div class="meta-line">Rendered duration: ${escapeHtml(String(render.duration_seconds))}s · ${escapeHtml(String(composition.total_bars))} bars</div>
      <div class="file-links">
        <a href="${result.wav_url}" target="_blank" rel="noreferrer">Open WAV</a>
        <a href="${result.midi_url}" target="_blank" rel="noreferrer">Open MIDI</a>
        <a href="${result.info_url}" target="_blank" rel="noreferrer">Open Metadata</a>
        ${stemLinks}
      </div>
    </article>
  `;
}

function renderLibrary(items) {
  if (!items.length) {
    elements.libraryList.innerHTML = `<div class="empty-state">No generated tracks yet.</div>`;
    return;
  }

  elements.libraryList.innerHTML = items
    .map((item) => {
      const stemLinks = (item.stem_urls || [])
        .slice(0, 3)
        .map((url) => `<a href="${url}" target="_blank" rel="noreferrer">${escapeHtml(fileName(url))}</a>`)
        .join("");

      return `
        <article class="library-item">
          <div class="library-header">
            <div>
              <p class="label">Recent Track</p>
              <h3>${escapeHtml(item.title || "Untitled")}</h3>
              <div class="mini-meta">${escapeHtml(item.generated_at || "")}</div>
            </div>
            <div class="mini-meta">${escapeHtml(item.key || "")} ${escapeHtml(item.mode || "")} · ${escapeHtml(String(item.bpm || ""))} BPM</div>
          </div>
          <div class="meta-line">${escapeHtml(item.description || "")}</div>
          <div class="meta-line">${escapeHtml(item.immersion || "music")} · ${escapeHtml((item.ambience || []).join(", ") || "no ambience")}</div>
          <div class="meta-line">${escapeHtml((item.palette || []).join(" · ") || "")}</div>
          ${item.wav_url ? `<audio controls preload="none" src="${item.wav_url}"></audio>` : ""}
          <div class="file-links">
            ${item.wav_url ? `<a href="${item.wav_url}" target="_blank" rel="noreferrer">WAV</a>` : ""}
            ${item.midi_url ? `<a href="${item.midi_url}" target="_blank" rel="noreferrer">MIDI</a>` : ""}
            ${item.info_url ? `<a href="${item.info_url}" target="_blank" rel="noreferrer">Metadata</a>` : ""}
            ${stemLinks}
          </div>
        </article>
      `;
    })
    .join("");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function fileName(url) {
  return url.split("/").pop() || url;
}

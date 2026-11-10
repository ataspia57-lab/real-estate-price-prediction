(() => {
  const $ = (s) => document.querySelector(s);
  const LOCS = window.LOCATIONS || [];
  const B = window.BOUNDS || {};

  /* ---------- BDT formatting (lakh / crore) ---------- */
  const bdt = (n) => "৳ " + Math.round(n).toLocaleString("en-IN");
  const words = (n) => {
    if (n >= 1e7) return `≈ ${(n / 1e7).toFixed(2)} crore taka`;
    if (n >= 1e5) return `≈ ${(n / 1e5).toFixed(1)} lakh taka`;
    return `≈ ${Math.round(n).toLocaleString("en-IN")} taka`;
  };
  const short = (n) => (n >= 1e7 ? `৳${(n / 1e7).toFixed(2)} cr` : `৳${(n / 1e5).toFixed(1)} lakh`);

  /* ---------- Searchable location combobox (FR-2) ---------- */
  const input = $("#loc-input"), list = $("#loc-list");
  let matches = [], active = -1, chosen = "";

  function render() {
    const q = input.value.trim().toLowerCase();
    matches = LOCS.filter((l) => l.toLowerCase().includes(q));
    // Put prefix matches first
    matches.sort((a, b) => (b.toLowerCase().startsWith(q)) - (a.toLowerCase().startsWith(q)));
    list.innerHTML = "";
    if (!matches.length) {
      list.innerHTML = '<li class="none">No match. Try “Other”.</li>';
    }
    matches.forEach((m, i) => {
      const li = document.createElement("li");
      li.id = `loc-opt-${i}`;
      li.role = "option";
      li.textContent = m;
      li.setAttribute("aria-selected", i === active);
      li.addEventListener("mousedown", (e) => { e.preventDefault(); pick(m); });
      list.appendChild(li);
    });
    open(true);
  }
  function open(on) {
    list.hidden = !on;
    input.setAttribute("aria-expanded", on);
    if (!on) input.removeAttribute("aria-activedescendant");
  }
  function pick(m) {
    chosen = m; input.value = m; active = -1; open(false);
    input.removeAttribute("aria-invalid");
  }
  function highlight(i) {
    active = Math.max(0, Math.min(i, matches.length - 1));
    [...list.children].forEach((li, j) => li.setAttribute("aria-selected", j === active));
    const el = list.children[active];
    if (el) { el.scrollIntoView({ block: "nearest" }); input.setAttribute("aria-activedescendant", el.id); }
  }
  input.addEventListener("input", () => { chosen = ""; active = -1; render(); });
  input.addEventListener("focus", render);
  input.addEventListener("blur", () => {
    // Accept an exact (case-insensitive) typed match
    const exact = LOCS.find((l) => l.toLowerCase() === input.value.trim().toLowerCase());
    if (exact) pick(exact);
    open(false);
  });
  input.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown") { e.preventDefault(); if (list.hidden) render(); highlight(active + 1); }
    else if (e.key === "ArrowUp") { e.preventDefault(); highlight(active - 1); }
    else if (e.key === "Enter" && !list.hidden && active >= 0) { e.preventDefault(); pick(matches[active]); }
    else if (e.key === "Escape") open(false);
  });

  /* ---------- Steppers ---------- */
  document.querySelectorAll(".stepper").forEach((s) => {
    const field = $("#" + s.dataset.target);
    const min = +s.dataset.min, max = +s.dataset.max;
    const [dec, inc] = s.querySelectorAll("button");
    const sync = () => { dec.disabled = +field.value <= min; inc.disabled = +field.value >= max; };
    s.addEventListener("click", (e) => {
      const step = e.target.dataset.step;
      if (!step) return;
      field.value = Math.min(max, Math.max(min, +field.value + +step));
      sync();
    });
    sync();
  });

  /* ---------- Client-side validation (FR-3) ---------- */
  const err = $("#form-error"), sqft = $("#sqft");
  function fail(msg, el) {
    err.textContent = msg; err.hidden = false;
    if (el) { el.setAttribute("aria-invalid", "true"); el.focus(); }
    return false;
  }
  function validate() {
    err.hidden = true;
    [input, sqft].forEach((el) => el.removeAttribute("aria-invalid"));
    if (!chosen) return fail("Choose a location from the list.", input);
    const s = Number(sqft.value), bhk = Number($("#bhk").value);
    if (!sqft.value || !Number.isFinite(s) || s <= 0) return fail("Enter the size in square feet (a positive number).", sqft);
    if (B.total_sqft && (s < B.total_sqft[0] || s > B.total_sqft[1]))
      return fail(`Size must be between ${B.total_sqft[0].toLocaleString()} and ${B.total_sqft[1].toLocaleString()} sqft.`, sqft);
    if (s / bhk < (B.sqft_per_bhk_min || 300))
      return fail(`${s.toLocaleString()} sqft is too small for ${bhk} bedrooms.`, sqft);
    return true;
  }

  /* ---------- Submit ---------- */
  const btn = $("#submit");
  $("#form").addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!validate()) return;
    btn.disabled = true; btn.textContent = "Estimating…";
    const payload = {
      location: chosen, total_sqft: Number(sqft.value),
      bhk: Number($("#bhk").value), bath: Number($("#bath").value),
    };
    try {
      // Static/offline build (single HTML page) supplies window.localApi instead of the Flask server.
      if (window.localApi) {
        const out = window.localApi.predict(payload);
        if (out.error) return fail(out.error);
        show(out);
        loadHistory();
        return;
      }
      const res = await fetch("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) return fail(data.error || "Something went wrong.");
      show(data);
      loadHistory();
    } catch {
      fail("Could not reach the server. Is it running?");
    } finally {
      btn.disabled = false; btn.textContent = "Estimate price";
    }
  });

  function show(d) {
    $("#empty").hidden = true;
    const f = $("#filled");
    f.hidden = false; f.classList.remove("reveal"); void f.offsetWidth; f.classList.add("reveal");
    $("#r-where").textContent = `${$("#bhk").value} bed · ${$("#bath").value} bath · ${chosen}`;
    $("#r-price").textContent = bdt(d.price);
    $("#r-words").textContent = words(d.price);
    $("#r-range").textContent = `${short(d.range[0])} – ${short(d.range[1])}`;
    $("#r-pps").textContent = bdt(d.price_per_sqft);
    $("#r-model").textContent = d.model;
    $("#r-ms").textContent = `${d.latency_ms} ms`;
    $("#r-disclaimer").textContent = d.disclaimer;
  }

  /* ---------- History ---------- */
  async function loadHistory() {
    try {
      const { items } = window.localApi ? window.localApi.history()
        : await (await fetch("/api/history")).json();
      if (!items.length) return;
      $("#history-body").innerHTML = items.map((r) => `
        <tr><td>${escape(r.location)}</td><td>${Math.round(r.total_sqft).toLocaleString()} sqft</td>
        <td>${r.bhk} / ${r.bath ?? "–"}</td><td>${short(r.price_bdt)}</td></tr>`).join("");
    } catch { /* non-critical */ }
  }
  const escape = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  loadHistory();
})();

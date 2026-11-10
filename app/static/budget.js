/* Budget finder: where can a buyer afford a flat? (uses /api/budget, or window.localApi in the static build) */
(() => {
  const $ = (s) => document.querySelector(s);
  const form = $("#budget-form");
  if (!form) return;

  const amount = $("#b-amount"), hint = $("#b-amount-hint"), err = $("#b-error");
  const btn = $("#b-submit");
  let data = null, sortBy = "premium";

  const taka = (n) => "৳ " + Math.round(n).toLocaleString("en-IN");
  const short = (n) => (n >= 1e7 ? `৳${(n / 1e7).toFixed(2)} cr` : `৳${(n / 1e5).toFixed(1)} lakh`);
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  amount.addEventListener("input", () => {
    const v = Number(amount.value);
    hint.textContent = v > 0 ? `= ${taka(v * 1e5)} (${v >= 100 ? (v / 100).toFixed(2) + " crore" : v + " lakh"})` : "e.g. 120 lakh = 1.2 crore";
  });

  function fail(msg) { err.textContent = msg; err.hidden = false; amount.setAttribute("aria-invalid", "true"); }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    err.hidden = true; amount.removeAttribute("aria-invalid");
    const lakh = Number(amount.value);
    if (!amount.value || !Number.isFinite(lakh) || lakh <= 0) return fail("Enter your budget in lakh taka, e.g. 120.");
    if (lakh < 5) return fail("That budget is below the cheapest flats in the data. Try at least 20 lakh.");
    const payload = { budget: lakh * 1e5, bhk: Number($("#b-bhk").value) };
    const min = Number($("#b-min").value);
    if ($("#b-min").value && min > 0) payload.min_sqft = min;

    btn.disabled = true; btn.textContent = "Searching…";
    try {
      let out;
      if (window.localApi && window.localApi.budget) out = window.localApi.budget(payload);
      else {
        const res = await fetch("/api/budget", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
        out = await res.json();
        if (!res.ok) return fail(out.error || "Something went wrong.");
      }
      if (out.error) return fail(out.error);
      data = out; render();
    } catch { fail("Could not reach the server. Is it running?"); }
    finally { btn.disabled = false; btn.textContent = "Find areas"; }
  });

  document.querySelectorAll(".b-sort button").forEach((b) => b.addEventListener("click", () => {
    sortBy = b.dataset.sort;
    document.querySelectorAll(".b-sort button").forEach((x) => x.setAttribute("aria-pressed", x === b));
    if (data) render();
  }));

  function render() {
    const { counts, areas, bhk, typical_sqft: typ, budget } = data;
    const rank = { fits: 0, smaller: 1, over: 2 };
    const list = [...areas].sort((a, b) =>
      rank[a.status] - rank[b.status] ||
      (sortBy === "premium" ? b.price_per_sqft - a.price_per_sqft : (b.max_sqft || 0) - (a.max_sqft || 0)) ||
      a.min_price - b.min_price);

    const ok = counts.fits + counts.smaller;
    $("#b-headline").innerHTML = ok
      ? `With <b>${short(budget)}</b> you can buy a ${bhk}-bed flat in <b>${ok} of ${areas.length}</b> areas. A typical size (~${typ.toLocaleString()} sqft) fits in <b>${counts.fits}</b>.`
      : `<b>${short(budget)}</b> isn't enough for a ${bhk}-bed flat in any area. The cheapest starts at <b>${short(Math.min(...areas.map((a) => a.min_price)))}</b>. Try fewer bedrooms or a higher budget.`;
    $("#b-typ-head").textContent = `Typical ${typ.toLocaleString()} sqft costs`;

    $("#b-body").innerHTML = list.map((a) => `
      <tr class="st-${a.status}">
        <td><i class="dot ${a.status}" aria-hidden="true"></i>${esc(a.location)}</td>
        <td>${a.max_sqft ? `<b>${a.max_sqft.toLocaleString()} sqft</b>` : `<span class="muted">needs ${short(a.min_price)}+</span>`}</td>
        <td>${a.price_at_max ? short(a.price_at_max) : "–"}</td>
        <td>${short(a.typical_price)}</td>
        <td>${taka(a.price_per_sqft)}</td>
      </tr>`).join("");
    $("#b-disclaimer").textContent = data.disclaimer || "Estimates from historical data, not listings or a certified appraisal.";
    $("#b-results").hidden = false;
    $("#b-results").scrollIntoView({ behavior: "smooth", block: "start" });
  }
})();

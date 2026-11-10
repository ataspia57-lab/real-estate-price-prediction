/*
 * In-browser version of the Flask API, used by the single-file static build
 * (scripts/build_static.py). The trained Gradient Boosting trees are exported
 * to JSON and evaluated here, so the page needs no server.
 * Validation mirrors validate() in app/server.py.
 */
(() => {
  const M = window.MODEL;
  const B = M.bounds;
  const hist = [];

  function raw(x) {
    let s = M.init;
    for (const t of M.trees) {
      let n = 0;
      while (t.l[n] !== -1) n = x[t.f[n]] <= t.t[n] ? t.l[n] : t.r[n];
      s += M.lr * t.v[n];
    }
    return Math.expm1(s);
  }

  function validate(p) {
    if (!p.location) return "'location' is required.";
    if (!M.locations.includes(p.location)) return `'${p.location}' is not in the training data.`;
    const { total_sqft: sqft, bhk, bath } = p;
    if (!Number.isFinite(sqft) || sqft <= 0) return "'total_sqft' must be greater than zero.";
    if (!Number.isInteger(bhk) || bhk <= 0) return "'bhk' must be a whole number greater than zero.";
    if (sqft < B.total_sqft[0] || sqft > B.total_sqft[1])
      return `Size ${Math.round(sqft).toLocaleString()} sqft is outside what the model was trained on (${B.total_sqft[0].toLocaleString()}-${B.total_sqft[1].toLocaleString()} sqft), so a prediction would not be reliable.`;
    if (bhk < B.bhk[0] || bhk > B.bhk[1]) return `Bedrooms must be between ${B.bhk[0]} and ${B.bhk[1]}.`;
    if (sqft / bhk < B.sqft_per_bhk_min)
      return `${Math.round(sqft).toLocaleString()} sqft is too small for ${bhk} bedrooms (need at least ${B.sqft_per_bhk_min} sqft per bedroom).`;
    const maxBath = Math.min(B.bath[1], bhk + 2);
    if (bath != null && (bath < B.bath[0] || bath > maxBath))
      return `Bathrooms must be between ${B.bath[0]} and ${maxBath} for a ${bhk}-bedroom property.`;
    return null;
  }

  window.localApi = {
    predict(p) {
      const t0 = performance.now();
      const err = validate(p);
      if (err) return { error: err };
      const loc = M.cats.includes(p.location) ? p.location : "__none__"; // "Other" is a category too
      const x = M.cats.map((c) => (c === loc ? 1 : 0))
        .concat([p.total_sqft, p.bhk, p.bath ?? M.median[2]]);
      const price = Math.max(Math.round(raw(x) / 1000) * 1000, 0);
      const k = M.mae_pct / 100;
      const out = {
        price, currency: "BDT",
        range: [Math.round(price * (1 - k) / 1000) * 1000, Math.round(price * (1 + k) / 1000) * 1000],
        price_per_sqft: Math.round(price / p.total_sqft),
        model: M.best, latency_ms: Math.round((performance.now() - t0) * 10) / 10,
        bath_imputed: p.bath == null,
        disclaimer: "Statistical estimate from historical data, not a certified legal appraisal.",
      };
      hist.unshift({ location: p.location, total_sqft: p.total_sqft, bhk: p.bhk, bath: p.bath, price_bdt: price });
      hist.length = Math.min(hist.length, 20);
      return out;
    },
    history() { return { items: hist }; },

    // Mirrors src/budget.py
    budget({ budget, bhk, min_sqft }) {
      if (!Number.isFinite(budget) || budget < 1e5) return { error: "Enter your budget in lakh taka, e.g. 120." };
      if (!Number.isInteger(bhk) || bhk < B.bhk[0] || bhk > B.bhk[1]) return { error: `Bedrooms must be between ${B.bhk[0]} and ${B.bhk[1]}.` };
      const typical = (n) => Math.round((350 + 420 * n) / 50) * 50;
      const lo = Math.max(B.total_sqft[0], B.sqft_per_bhk_min * bhk, min_sqft || 0);
      const hi = Math.min(B.total_sqft[1], Math.trunc(typical(bhk) * 1.75));
      if (lo > hi) return { error: `No ${bhk}-bedroom size in the data is at least ${Math.round(min_sqft).toLocaleString()} sqft.` };
      const typ = Math.trunc(Math.min(Math.max(typical(bhk), lo), hi));
      const bath = bhk <= 2 ? bhk : bhk - 1;
      const grid = [];
      for (let s = lo; s <= hi; s += 25) grid.push(s);
      if (grid[grid.length - 1] !== hi) grid.push(hi);
      const r3 = (n) => Math.round(n / 1000) * 1000;
      const price = (loc, s) => raw(M.cats.map((c) => (c === loc ? 1 : 0)).concat([s, bhk, bath]));

      const areas = M.locations.filter((l) => l !== "Other").map((loc) => {
        const ps = grid.map((s) => price(loc, s));
        const tp = price(loc, typ);
        let i = -1;
        ps.forEach((p, j) => { if (p <= budget) i = j; });
        const a = { location: loc, typical_price: r3(tp), min_price: r3(ps[0]), price_per_sqft: Math.round(tp / typ),
                    max_sqft: null, price_at_max: null, status: "over" };
        if (i >= 0) Object.assign(a, { max_sqft: Math.round(grid[i]), price_at_max: r3(ps[i]), status: tp <= budget ? "fits" : "smaller" });
        return a;
      });
      const counts = { fits: 0, smaller: 0, over: 0 };
      areas.forEach((a) => counts[a.status]++);
      return { budget, bhk, bath, typical_sqft: typ, min_sqft: lo, counts, areas,
               disclaimer: "Estimates from historical data, not listings or a certified appraisal." };
    },
  };
})();

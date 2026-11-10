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
  };
})();

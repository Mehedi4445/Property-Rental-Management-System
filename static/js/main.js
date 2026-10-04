document.addEventListener("DOMContentLoaded", () => {
  // navbar shadow on scroll
  const nav = document.querySelector(".site-nav");
  const onScroll = () => nav && nav.classList.toggle("scrolled", window.scrollY > 8);
  onScroll(); window.addEventListener("scroll", onScroll, {passive: true});

  // flash messages as toasts
  document.querySelectorAll(".toast").forEach(t => new bootstrap.Toast(t).show());

  // confirm dangerous actions
  document.querySelectorAll("form[data-confirm]").forEach(f =>
    f.addEventListener("submit", e => { if (!confirm(f.dataset.confirm)) e.preventDefault(); }));

  // show/hide password
  document.querySelectorAll("input[type=password]").forEach(input => {
    const wrap = document.createElement("div"); wrap.className = "pw-wrap";
    input.parentNode.insertBefore(wrap, input); wrap.appendChild(input);
    const btn = document.createElement("button");
    btn.type = "button"; btn.className = "pw-toggle"; btn.setAttribute("aria-label", "Show password");
    btn.innerHTML = '<i class="bi bi-eye"></i>';
    btn.addEventListener("click", () => {
      const show = input.type === "password";
      input.type = show ? "text" : "password";
      btn.innerHTML = `<i class="bi bi-eye${show ? "-slash" : ""}"></i>`;
    });
    wrap.appendChild(btn);
  });

  // count-up for dashboard numbers
  document.querySelectorAll("[data-count]").forEach(el => {
    const end = parseInt(el.dataset.count, 10) || 0;
    if (!end || matchMedia("(prefers-reduced-motion: reduce)").matches) { el.textContent = end; return; }
    const t0 = performance.now(), dur = 700;
    const tick = now => {
      const p = Math.min((now - t0) / dur, 1);
      el.textContent = Math.round(end * (1 - Math.pow(1 - p, 3)));
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  });

  // image upload preview
  document.querySelectorAll("input[type=file][data-preview]").forEach(input => {
    const img = document.createElement("img"); img.className = "preview"; img.alt = "Preview";
    input.parentNode.appendChild(img);
    input.addEventListener("change", () => {
      const f = input.files[0];
      if (f) { img.src = URL.createObjectURL(f); img.style.display = "block"; }
    });
  });

  // filters apply as soon as a select changes
  document.querySelectorAll("form[data-autosubmit] select").forEach(s =>
    s.addEventListener("change", () => s.form.submit()));

  // keep the chosen dashboard tab after a reload
  const tabs = document.querySelectorAll('[data-bs-toggle="tab"]');
  const saved = localStorage.getItem("dash-tab");
  tabs.forEach(t => {
    if (saved && t.dataset.bsTarget === saved) bootstrap.Tab.getOrCreateInstance(t).show();
    t.addEventListener("shown.bs.tab", () => localStorage.setItem("dash-tab", t.dataset.bsTarget));
  });
});

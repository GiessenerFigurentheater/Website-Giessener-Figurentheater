const $$ = s => [...document.querySelectorAll(s)];

// Mobiles Menü
const menu = document.getElementById("menu");
document.querySelector(".menu-btn")?.addEventListener("click", () => menu.classList.toggle("open"));

// Reiter (Tabs)
function showTab(t) {
  $$(".tab").forEach(b => b.setAttribute("aria-selected", b.dataset.t === t));
  $$(".panel").forEach(p => p.hidden = p.dataset.p !== t);
}
$$(".tab").forEach(b => b.addEventListener("click", () => showTab(b.dataset.t)));

// Anfrageformulare (Buchung, Mietanfrage): Stück aus der URL vorauswählen (?stueck=das-neinhorn)
document.querySelectorAll("form.request").forEach(form => {
  const wanted = new URLSearchParams(location.search).get("stueck");
  const select = form.querySelector("[name=Stueck]");
  if (wanted && select) {
    const opt = [...select.options].find(o => o.dataset.slug === wanted);
    if (opt) select.value = opt.value;
  }
  // Absenden: an den Formular-Dienst (Adresse steht in <body data-formular>), sonst E-Mail-Programm öffnen
  const adresse = document.body.dataset.formular;
  // Spamschutz (Honeypot): verstecktes Feld, das nur Spam-Programme ausfüllen – Fakturus verwirft solche Anfragen
  form.insertAdjacentHTML("beforeend", '<input type="text" name="_hp" style="display:none" tabindex="-1" autocomplete="off" aria-hidden="true">');
  const zusammenfassung = d => [...d].filter(([k]) => !["Datenschutz", "Betreff", "_hp"].includes(k)).map(([k, v]) => `${k}: ${v}`).join("\n");
  const betreff = () => (form.dataset.betreff || "Buchungsanfrage") + ": " + (new FormData(form).get("Einrichtung") || "");
  const perMail = () => {
    const d = new FormData(form);
    const body = zusammenfassung(d);
    location.href = "mailto:info@giessener-figurentheater.de?subject=" + encodeURIComponent(betreff()) + "&body=" + encodeURIComponent(body);
  };
  form.addEventListener("submit", async e => {
    e.preventDefault();
    if (!adresse) return perMail();
    const knopf = form.querySelector("[type=submit]");
    const d = new FormData(form);
    // Fakturus erwartet die Felder name, email und message – alle Angaben stehen zusätzlich gesammelt in message
    d.set("Betreff", betreff());
    d.set("name", d.get("Ansprechperson") || d.get("Einrichtung") || "");
    d.set("email", d.get("E-Mail") || "");
    d.set("message", betreff() + "\n\n" + zusammenfassung(new FormData(form)));
    knopf.disabled = true;
    knopf.textContent = "Wird gesendet …";
    try {
      // Fakturus erlaubt keine Antwort an fremde Seiten (CORS) – „no-cors“ schickt die Anfrage trotzdem zuverlässig ab
      await fetch(adresse, { method: "POST", body: d, mode: "no-cors" });
      form.innerHTML = '<div class="danke full"><h3>Vielen Dank für eure Anfrage!</h3>' +
        '<p>Wir haben eure Nachricht erhalten und melden uns so schnell wie möglich – meist innerhalb von 1–2 Tagen.</p></div>';
      form.scrollIntoView({ block: "center" });
    } catch (fehler) {
      // Klappt das Senden nicht (z. B. keine Verbindung), bleibt der Weg über das E-Mail-Programm
      knopf.disabled = false;
      knopf.textContent = "Erneut senden";
      if (confirm("Die Anfrage konnte gerade nicht gesendet werden. Stattdessen euer E-Mail-Programm mit allen Angaben öffnen?")) perMail();
    }
  });
});

// Wischen auf Handy & Tablet: waagerechte Wischbewegung blättert vor bzw. zurück,
// senkrechtes Wischen scrollt die Seite ganz normal weiter.
const wischen = (el, zurueck, vor) => {
  let x0 = null, y0 = 0;
  el.style.touchAction = "pan-y";
  el.addEventListener("touchstart", ev => { x0 = ev.touches[0].clientX; y0 = ev.touches[0].clientY; }, { passive: true });
  el.addEventListener("touchend", ev => {
    if (x0 === null) return;
    const dx = ev.changedTouches[0].clientX - x0, dy = ev.changedTouches[0].clientY - y0;
    x0 = null;
    if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(dy) * 1.2) (dx < 0 ? vor : zurueck)();
  }, { passive: true });
};

// Bildershow: automatischer Wechsel, Punkte zum Springen, Pause-Knopf, Wischen
const slider = document.querySelector(".slider");
if (slider) {
  const slides = [...slider.querySelectorAll(".slide")];
  const dots = [...slider.querySelectorAll(".slider-dots button")];
  const pauseBtn = slider.querySelector(".slider-pause");
  const ruhig = matchMedia("(prefers-reduced-motion: reduce)").matches;
  let aktuell = 0, timer = null, pausiert = ruhig;

  const zeige = i => {
    aktuell = (i + slides.length) % slides.length;
    slides.forEach((s, n) => s.classList.toggle("is-active", n === aktuell));
    dots.forEach((d, n) => d.setAttribute("aria-selected", n === aktuell));
  };
  const starte = () => { clearInterval(timer); if (!pausiert) timer = setInterval(() => zeige(aktuell + 1), 6000); };
  const setzePause = p => {
    pausiert = p;
    pauseBtn.textContent = p ? "▶" : "❚❚";
    pauseBtn.setAttribute("aria-label", p ? "Bildershow fortsetzen" : "Bildershow anhalten");
    starte();
  };

  dots.forEach((d, n) => d.addEventListener("click", () => { zeige(n); starte(); }));
  pauseBtn.addEventListener("click", () => setzePause(!pausiert));
  slider.addEventListener("mouseenter", () => clearInterval(timer));
  slider.addEventListener("mouseleave", starte);
  wischen(slider, () => { zeige(aktuell - 1); starte(); }, () => { zeige(aktuell + 1); starte(); });
  setzePause(pausiert);
}

// Galerie: Foto groß anzeigen, mit Pfeiltasten oder Wischen blättern, Esc schließt
const lbLinks = [...document.querySelectorAll("a[data-lightbox]")];
if (lbLinks.length) {
  const lb = document.createElement("div");
  lb.className = "lightbox";
  lb.hidden = true;
  lb.setAttribute("role", "dialog");
  lb.setAttribute("aria-label", "Foto-Ansicht");
  lb.innerHTML = '<figure style="margin:0"><img alt=""><p></p></figure>' +
    '<button class="lb-close" aria-label="Schließen">✕</button>' +
    '<button class="lb-prev" aria-label="Vorheriges Foto">‹</button><button class="lb-next" aria-label="Nächstes Foto">›</button>';
  document.body.append(lb);
  const img = lb.querySelector("img"), txt = lb.querySelector("p");
  let i = 0;
  const zeige = n => {
    i = (n + lbLinks.length) % lbLinks.length;
    const a = lbLinks[i], klein = a.querySelector("img");
    img.src = a.href;
    img.alt = klein.alt;
    txt.textContent = a.parentElement.querySelector("figcaption")?.textContent || "";
    lb.hidden = false;
  };
  lbLinks.forEach((a, n) => a.addEventListener("click", ev => { ev.preventDefault(); zeige(n); }));
  lb.querySelector(".lb-close").onclick = () => lb.hidden = true;
  lb.querySelector(".lb-prev").onclick = () => zeige(i - 1);
  lb.querySelector(".lb-next").onclick = () => zeige(i + 1);
  lb.addEventListener("click", ev => { if (ev.target === lb) lb.hidden = true; });
  wischen(lb, () => zeige(i - 1), () => zeige(i + 1));
  document.addEventListener("keydown", ev => {
    if (lb.hidden) return;
    if (ev.key === "Escape") lb.hidden = true;
    if (ev.key === "ArrowLeft") zeige(i - 1);
    if (ev.key === "ArrowRight") zeige(i + 1);
  });
}

// Google-Bewertungen: wechseln alle 8 Sekunden, Pfeile, Punkte und Wischen zum Blättern
const reviewBox = document.querySelector(".review-slider");
if (reviewBox) {
  const items = [...reviewBox.querySelectorAll(".review")];
  const dots = [...reviewBox.querySelectorAll(".review-dots button")];
  const ruhig = matchMedia("(prefers-reduced-motion: reduce)").matches;
  let n = 0, t = null;
  const zeige = i => {
    n = (i + items.length) % items.length;
    items.forEach((r, k) => r.classList.toggle("is-active", k === n));
    dots.forEach((d, k) => d.setAttribute("aria-selected", k === n));
  };
  const los = () => { clearInterval(t); if (!ruhig && items.length > 1) t = setInterval(() => zeige(n + 1), 8000); };
  reviewBox.querySelector(".review-prev").addEventListener("click", () => { zeige(n - 1); los(); });
  reviewBox.querySelector(".review-next").addEventListener("click", () => { zeige(n + 1); los(); });
  dots.forEach((d, k) => d.addEventListener("click", () => { zeige(k); los(); }));
  reviewBox.addEventListener("mouseenter", () => clearInterval(t));
  reviewBox.addEventListener("mouseleave", los);
  wischen(reviewBox, () => { zeige(n - 1); los(); }, () => { zeige(n + 1); los(); });
  los();
}

// Galerie-Wand, Startseiten-Vorschau & Stück-Kacheln: Kacheln wackeln kurz, sobald sie beim Scrollen ins Bild kommen
document.querySelectorAll(".wand, .mosaic, .plays").forEach(wand => {
  if (!("IntersectionObserver" in window) || matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const kacheln = [...wand.querySelectorAll("figure, .play")];
  wand.classList.add("bereit");
  const beob = new IntersectionObserver(eintraege => {
    let reihe = 0;
    eintraege.forEach(e => {
      if (e.isIntersecting) {
        e.target.style.setProperty("--verz", `${(reihe++ % 6) * 0.08}s`);
        e.target.classList.add("sichtbar");
      } else if (e.boundingClientRect.top > 0) {
        // Beim Zurückscrollen nach oben wieder zurücksetzen, damit es beim nächsten Mal erneut wackelt
        e.target.classList.remove("sichtbar");
      }
    });
  }, { threshold: 0.15 });
  kacheln.forEach(k => beob.observe(k));
});

// KULTURzelt: Zelt-Fotos durchwischen – Pfeile, Punkte und Wischen
document.querySelectorAll(".karussell").forEach(k => {
  const spur = k.querySelector(".spur");
  const punkte = [...k.querySelectorAll(".k-punkte button")];
  const prev = k.querySelector(".k-prev"), next = k.querySelector(".k-next");
  const aktuell = () => Math.round(spur.scrollLeft / spur.clientWidth);
  const gehe = n => spur.scrollTo({ left: n * spur.clientWidth });
  const markiere = () => {
    const n = aktuell();
    punkte.forEach((p, i) => p.setAttribute("aria-current", i === n));
    prev.disabled = n === 0;
    next.disabled = n === punkte.length - 1;
  };
  prev.addEventListener("click", () => gehe(aktuell() - 1));
  next.addEventListener("click", () => gehe(aktuell() + 1));
  punkte.forEach((p, i) => p.addEventListener("click", () => gehe(i)));
  spur.addEventListener("keydown", ev => {
    if (ev.key === "ArrowRight") { gehe(aktuell() + 1); ev.preventDefault(); }
    if (ev.key === "ArrowLeft") { gehe(aktuell() - 1); ev.preventDefault(); }
  });
  spur.addEventListener("scroll", () => requestAnimationFrame(markiere), { passive: true });
  markiere();
});

// Startseite: Samtvorhang öffnet sich beim Scrollen. --auf läuft von 0 (zu) bis 1 (offen);
// die Bildershow bleibt dabei stehen (sticky), bis der Vorhang ganz offen ist.
const buehne = document.querySelector(".vorhang-buehne");
if (buehne && !matchMedia("(prefers-reduced-motion: reduce)").matches) {
  const kopf = document.querySelector("header.top");
  const setzeKopf = () => document.documentElement.style.setProperty("--kopf", `${kopf ? kopf.offsetHeight : 0}px`);
  let geplant = false;
  const oeffne = () => {
    geplant = false;
    const weg = buehne.offsetHeight - buehne.querySelector(".slider").offsetHeight;
    const roh = Math.min(Math.max(((kopf ? kopf.offsetHeight : 0) - buehne.getBoundingClientRect().top) / (weg * 0.8), 0), 1);
    const auf = roh * roh * (3 - 2 * roh); // sanft beschleunigen und abbremsen
    buehne.style.setProperty("--auf", auf.toFixed(4));
  };
  const plane = () => { if (!geplant) { geplant = true; requestAnimationFrame(oeffne); } };
  setzeKopf();
  oeffne();
  addEventListener("scroll", plane, { passive: true });
  addEventListener("resize", () => { setzeKopf(); plane(); });
}

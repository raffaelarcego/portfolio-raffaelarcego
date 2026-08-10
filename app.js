/* Idioma + navegação por abas. Sem dependências. */
(function () {
  "use strict";

  var body = document.body;
  var gate = document.getElementById("lang-gate");
  var TABS = ["sobre", "projetos", "curriculo", "carta", "contato"];

  /* ---------- idioma ---------- */

  function setLang(lang) {
    body.classList.remove("lang-pt", "lang-en");
    body.classList.add(lang === "en" ? "lang-en" : "lang-pt");
    document.documentElement.lang = lang === "en" ? "en-US" : "pt-BR";
    document.title = lang === "en"
      ? "Raffael Michels — Data Analyst & Computer Vision"
      : "Raffael Michels — Analista de Dados & Visão Computacional";
    try { sessionStorage.setItem("lang", lang); } catch (e) { /* modo privado */ }

    var switches = document.querySelectorAll("[data-set-lang]");
    for (var i = 0; i < switches.length; i++) {
      var b = switches[i];
      b.classList.toggle("on", b.getAttribute("data-set-lang") === lang);
    }
  }

  function closeGate() {
    gate.hidden = true;
    body.classList.remove("gate-open");
  }

  var chooseButtons = gate.querySelectorAll("[data-choose]");
  for (var i = 0; i < chooseButtons.length; i++) {
    chooseButtons[i].addEventListener("click", function () {
      setLang(this.getAttribute("data-choose"));
      closeGate();
    });
  }

  var switchButtons = document.querySelectorAll("[data-set-lang]");
  for (var j = 0; j < switchButtons.length; j++) {
    switchButtons[j].addEventListener("click", function () {
      setLang(this.getAttribute("data-set-lang"));
    });
  }

  /* A porta aparece sempre que uma nova sessão do navegador começa.
     Dentro da mesma aba, a escolha é lembrada. Um link com ?lang=pt
     ou ?lang=en pula a porta (útil para compartilhar). */
  var saved = null;
  var fromUrl = /[?&]lang=(pt|en)/.exec(location.search);
  if (fromUrl) saved = fromUrl[1];
  try { if (!saved) saved = sessionStorage.getItem("lang"); } catch (e) { /* ignore */ }
  if (saved === "pt" || saved === "en") {
    setLang(saved);
    closeGate();
  } else {
    setLang("pt"); // texto de fundo enquanto a porta está aberta
  }

  /* ---------- abas ---------- */

  function showTab(id) {
    if (TABS.indexOf(id) === -1) id = TABS[0];
    /* Os ids das seções têm prefixo "tab-" para o navegador não rolar
       sozinho até a âncora ao abrir um link com #hash. */
    var sections = document.querySelectorAll("main section.tab");
    for (var s = 0; s < sections.length; s++) {
      sections[s].classList.toggle("visible", sections[s].id === "tab-" + id);
    }
    var links = document.querySelectorAll("nav [data-tab]");
    for (var l = 0; l < links.length; l++) {
      links[l].classList.toggle("active", links[l].getAttribute("data-tab") === id);
    }
    window.scrollTo(0, 0);
  }

  var navLinks = document.querySelectorAll("nav [data-tab]");
  for (var n = 0; n < navLinks.length; n++) {
    navLinks[n].addEventListener("click", function (ev) {
      ev.preventDefault();
      var id = this.getAttribute("data-tab");
      if (history.pushState) history.pushState(null, "", "#" + id);
      showTab(id);
    });
  }

  window.addEventListener("popstate", function () {
    showTab(location.hash.replace("#", "") || TABS[0]);
  });

  showTab(location.hash.replace("#", "") || TABS[0]);
})();

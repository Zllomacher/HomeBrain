# 🧠 HomeBrain

**Inteligentní rodinný archiv a asistent pro správu dokumentů, účtenek, smluv a lékařských zpráv.**

Mobilní webové rozhraní umožňující na dvě kliknutí vyfotit dokument, zařadit do složky, okamžitě odeslat e-mailem na zvolenou adresu (např. firemní vs. soukromý mail) a synchronizovat do lokálního archivu na PC pro pozdější vytěžení lokální AI (Ollama).

---

## 🚀 Klíčové vlastnosti

- 📱 **Rychlé mobilní webové rozhraní (PWA)**: Běží v prohlížeči telefonu bez nutnosti instalace z aplikačních obchodů.
- 🔒 **Rodinné zabezpečení**: Ochrana přístupovým PINem s dlouhodobým zapamatováním na zařízeních rodiny (ochrana před cizími návštěvníky).
- 📧 **Chytré e-mailové směrování (Router)**:
  - *Paragony & Parkování* -> Služební e-mail s přednastaveným předmětem.
  - *Lékařské zprávy & Smlouvy* -> Soukromý e-mail.
  - Snadná tvorba nových složek a vlastních pravidel přímo v rozhraní.
- 💻 **PC synchronizace (připraveno pro Fázi 2)**: Automatické stahování dokumentů do strukturovaných složek na PC po jeho zapnutí.
- 🧠 **Lokální AI & NotebookLM styl (připraveno pro Fázi 3)**: Ollama běžící na domácím PC vytěží texty (OCR) a odpovídá na dotazy (např. *„Kdy jde Radek na kontrolu?“*).

---

## 📖 Kompletní dokumentace

Detailní technická a funkční specifikace, diagram architektury a plán vývoje je k dispozici v:
👉 [**Dokumentace a projektová specifikace (docs/PROJECT_SPEC.md)**](docs/PROJECT_SPEC.md)

---

## 🗺️ Stav projektu

- [x] Projektová specifikace a architektura
- [ ] **Fáze 1**: Webová aplikace pro sběr dokumentů, PIN zabezpečení, správa složek a e-mailové směrování
- [ ] **Fáze 2**: Lokální synchronizační klient pro PC (Windows)
- [ ] **Fáze 3**: Integrace lokálního AI modelu (Ollama + OCR + RAG Q&A)
- [ ] **Fáze 4**: Multi-user režim a pokročilé rodinné sdílení
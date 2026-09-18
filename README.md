# 🧠 HomeBrain

**Inteligentní rodinný multi-user správce dokumentů, účtenek, smluv a lékařských zpráv.**

100% webová aplikace optimalizovaná pro mobilní telefony (focení v terénu) i počítače (Windows PC i Apple Mac v domácnosti). Umožňuje na dvě kliknutí vyfotit dokument, zařadit do složky, odeslat e-mailem na zvolenou adresu (služební vs. soukromý mail) a mít připravený webový inbox pro uložení do počítače a budoucí vytěžení lokální AI (Ollama).

---

## 🌟 Hlavní přednosti

- 👥 **Multi-user od začátku**: Každý člen rodiny (vy, manželka i další uživatelé) má svůj vlastní účet a vlastní nastavení cílových e-mailů.
- 📱 **Rychlé mobilní rozhraní (PWA)**: Bleskové otevření fotoaparátu přímo v prohlížeči telefonu bez instalace z obchodů.
- 💻 **100% Web-based (PC i Mac)**: Žádné instalování desktopových aplikací – pohodlný přístup odkudkoliv, ideální pro střídání počítačů i různé systémy (Windows, macOS).
- 📧 **Chytré e-mailové směrování (Router)**:
  - *Paragony / Parkování* -> Služební e-mail s přednastaveným předmětem.
  - *Lékařské zprávy / Smlouvy* -> Soukromý e-mail.
  - Možnost kdykoliv přidat novou záložku/složku přímo v rozhraní.
- 📥 **Webový Inbox („Co na mě čeká“)**: Přehled nahraných dokumentů s možností uložení do složek na disku PC/Macu.
- 🧠 **Připraveno pro lokální AI (Ollama)**: V budoucí fázi možnost napojení domácí Ollamy pro OCR a dotazy přirozeným jazykem (*„Kdy jde Radek na kontrolu?“*).

---

## 📖 Kompletní dokumentace

Podrobná specifikace, diagram architektury a roadmapa vývoje:  
👉 [**Detailní projektová specifikace (docs/PROJECT_SPEC.md)**](docs/PROJECT_SPEC.md)

---

## 🗺️ Stav projektu

- [x] Projektová specifikace a multi-user webová architektura
- [ ] **Fáze 1**: Webová aplikace (Backend FastAPI + SQLite, správa uživatelů a e-mailů, mobilní focení, odesílání e-mailem, webový inbox)
- [ ] **Fáze 2**: Pokročilá synchronizace a organizace složek na PC/Macu
- [ ] **Fáze 3**: Lokální AI (Ollama) s OCR a chatovacím asistentem ve stylu NotebookLM
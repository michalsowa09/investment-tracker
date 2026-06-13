# MONITOR INWESTYCJI (Investor Dashboard)

Zintegrowany System Informatyczny do zarządzania portfelem aktywów w czasie rzeczywistym. Projekt zbudowany w nowoczesnej architekturze asynchronicznej zgodnie z metodologią **The Twelve-Factor App**.

## Kluczowe Funkcje
- **Zarządzanie Portfelem (CRUD):** Dodawanie, edycja, usuwanie i przegląd aktywów.
- **Inteligentna Logika:** Automatyczne wyliczanie średniej ceny ważonej przy dokupowaniu aktywów.
- **Integracja z NBP:** Pobieranie kursów walut (USD, EUR, GBP, CHF) na żywo przez API Narodowego Banku Polskiego.
- **Analiza Finansowa:** Dynamiczne wyliczanie zysku/straty portfela.
- **Warstwa Cache:** Wykorzystanie bazy **Redis** do optymalizacji zapytań zewnętrznych.
- **Panel Administratora:** Zabezpieczony panel zarządzania danymi (SQLAdmin) z logowaniem.

## Stos Technologiczny
- **Backend:** Python 3.11 + FastAPI (Async)
- **Baza danych:** PostgreSQL 15 + SQLAlchemy 2.0 (ORM)
- **Cache:** Redis 7
- **Frontend:** Jinja2 Templates + Bootstrap 5 (Dark Mode)
- **Konteneryzacja:** Docker & Docker Compose
- **Automatyzacja:** GitHub Actions (CI/CD)

## Architektura (12-Factor App)
System spełnia nowoczesne standardy aplikacji chmurowych:
- **Dependencies:** Izolacja środowiska w Dockerze.
- **Config:** Konfiguracja przez zmienne środowiskowe (GitHub Secrets / Docker Env).
- **Backing Services:** Postgres i Redis jako zasoby dołączane.
- **Statelessness:** Aplikacja jest bezstanowa; dane trzymane w bazie.
# DetailFlow

**System operacyjny studia autodetailingu** — projekt praktyk studenckich / portfolio backend.

Django **MVT** + PostgreSQL + Redis/Celery + Tailwind (CDN). Aplikacja prowadzi pojazd od przyjęcia, przez wjazd na halę i rozliczenie materiałów, aż do wydania klientowi z powiadomieniem e-mail i opcjonalnym certyfikatem PDF powłoki ceramicznej.

> **MVP / wersja robocza** — środowisko deweloperskie pod Dockerem. Nie jest to gotowy produkt produkcyjny.

---

## Stack

| Warstwa | Technologia |
|--------|-------------|
| Backend | Django 5 (MVT) |
| Baza | PostgreSQL 16 |
| Kolejki | Celery + Redis |
| Dev SMTP | Mailpit |
| PDF | WeasyPrint |
| Front | Django Templates + Tailwind CDN |
| AI (opcjonalnie) | Google Gemini — blueprinty SVG auta |

---

## Co potrafi aplikacja

1. Kartoteka: klient → pojazd → zlecenie (tworzenie, edycja, anulowanie).
2. Hala operacyjna: filtry statusów (kolejka / w toku / gotowe / wydane).
3. Check-in: pomiar lakieru + interaktywna mapa uszkodzeń.
4. COGS: zużycie chemii, zejście ze stanu, marża wstępna.
5. Certyfikat ceramiki → PDF.
6. Mail „auto gotowe” (Celery) + podgląd w Mailpit.
7. Logowanie operatora — panel hali nie jest publiczny.

---

## Uruchomienie (2 kroki)

**Wymagania:** [Docker Desktop](https://www.docker.com/products/docker-desktop/), wolne porty **8000, 8025, 5555**.

```bash
git clone https://github.com/Gekel11/Detail-flow.git
cd Detail-flow          # nazwa katalogu po clone
docker compose up --build
```

Przy pierwszym starcie kontener `web` **automatycznie**:
- wykonuje migracje bazy,
- tworzy konto demo i przykładowe zlecenia (jeśli baza pusta).

Nie musisz ręcznie odpalać `migrate`, `createsuperuser` ani seeda.

### Logowanie

| Pole | Wartość |
|------|---------|
| Adres | http://localhost:8000/login/ |
| Użytkownik | `demo` |
| Hasło | `demo1234` |

Własne konto (opcjonalnie): `docker compose exec web python manage.py createsuperuser`

### Adresy

| Usługa | URL |
|--------|-----|
| Hala operacyjna | http://localhost:8000/ |
| Django Admin | http://localhost:8000/admin/ |
| Mailpit (maile) | http://localhost:8025/ |
| Flower (Celery) | http://localhost:5555/ |

### Plik `.env` (opcjonalny)

Domyślna konfiguracja dev jest w `docker-compose.yml`. Jeśli chcesz nadpisać (np. `GEMINI_API_KEY`):

```bash
cp .env.example .env
# edytuj .env
docker compose up --build
```

---

## Screenshots

![Hala operacyjna](docs/dashboard.png)

![Check-in / mapa uszkodzeń](docs/checkin.png)

![Mailpit — podgląd maila gotowości](docs/mailpit.png)

---

## Architektura

```
config/           # settings, urls, Celery
workshop/         # domena studia (modele, widoki, tasks, services)
inventory/        # stub
reports/          # stub
templates/        # UI
docker-entrypoint.sh   # migrate + seed_demo przed runserver
```

**Przepływ zlecenia:** PENDING → check-in → IN_PROGRESS → COGS → READY (mail Celery) → COMPLETED / CANCELLED

---

## Modele domenowe

| Model | Rola |
|-------|------|
| `Customer` / `Vehicle` | Kartoteka |
| `ServiceOrder` | Zlecenie i status |
| `PaintInspection` / `DamagePoint` | Protokół wjazdu |
| `CoatingCertificate` | PDF gwarancji |
| `ChemicalProduct` / `MaterialUsage` | Magazyn i COGS |
| `CarBlueprint` | Cache SVG (AI) |

---

## Dla developerów

```bash
docker compose exec web python manage.py test workshop
docker compose logs -f web
docker compose down        # stop (dane zostają)
docker compose down -v     # stop + kasuje bazę
```

Po zmianach w `tasks.py`: `docker compose restart worker`

---

## Limitacje MVP

- Dev stack (`runserver`, hasła w compose).
- Jedna rola operatora (+ admin).
- `inventory` / `reports` — placeholdery.
- Część paczek w `requirements.txt` (Stripe, pandas) — pod przyszłą rozbudowę.

---

## Autor

Projekt praktyk studenckich — DetailFlow Workshop OS (Django, Docker, Celery, PostgreSQL).

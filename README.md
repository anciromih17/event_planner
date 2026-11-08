# Termini predstav

Interni FastAPI sistem za spremljanje javno objavljenih terminov predstav in zaznavanje tehničnih konfliktov.

## Kaj sistem počne

- zbira termine iz skupnega Google Calendarja in s treh Vid Valič strani;
- Google Calendar bere prek uradnega Google Calendar API-ja;
- Vid Valič bere njihov javni WordPress/Tickera AJAX endpoint `tc_filter_events`;
- podvojene objave iste predstave iz različnih virov združi v en termin;
- označi `KONFLIKT`, kadar sta na isti datum vsaj dve različni predstavi (ura se namenoma ne upošteva);
- vsak dan ob 04:00 (Europe/Ljubljana) posodobi podatke;
- ponuja filtre, iskanje, koledarski prikaz in Excel/PDF izvoz.

## Analiza virov

| Vir | Ugotovitev | Implementacija |
| --- | --- | --- |
| Google Calendar | Interni skupni koledar z javno dostopnimi termini ŽBF 2. | Google Calendar API z OAuth poverilnicami lokalnega uporabnika. |
| Vid Valič | WordPress/Tickera. Osnovna stran vsebuje kategorijo, termini se naložijo z AJAX `tc_filter_events` na `wp-admin/admin-ajax.php`. | Neposreden `requests.post` na javni endpoint, nato BeautifulSoup parser. |

## Namestitev

Potreben je Python 3.11+.

```bash
cd event-planner
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

Po želji skopirajte `.env.example` v `.env` in nastavite `DATABASE_URL` (za privzeti SQLite to ni potrebno).

Za Google Calendar vir sta potrebni lokalni datoteki `credentials.json` in `token.json`. Zaradi varnosti sta izključeni iz Git repozitorija in ju je treba ustvariti oziroma prenesti ločeno.

## Zagon

```bash
uvicorn app.main:app --reload
```

Odprite `http://127.0.0.1:8000`. Prvi uvoz sprožite z gumbom **Osveži zdaj**. API dokumentacija je na `/docs`.

## Testi

```bash
pytest
```

## API

- `GET /api/events` – opcijski parametri `title`, `event_date`, `conflicts_only`, `search`
- `POST /api/refresh` – osveži vse javne vire
- `GET /api/calendar/{year}/{month}` – podatki za mesečni koledar
- `GET /export.xlsx`, `GET /export.pdf` – izvoza trenutnega seznama

## Opomba za obratovanje

Zbiranje uporablja samo javno dostopne podatke in ne poskuša obiti prijav ali zaščit. Strukture javnih strani se lahko spremenijo, zato so parserji izolirani v `app/scrapers/` in imajo osnovne teste; ob spremembi je treba prilagoditi samo ta sloj.

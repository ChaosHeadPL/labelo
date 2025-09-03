# Etykiety – FastAPI label service

MVP API generujące etykiety na podstawie JSON, z wyjściem PDF/PNG i prostym systemem "storage" (spiżarnia/warsztat) do kontroli braków.

## Szybki start (lokalnie)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
````

### Ikony i fonty

* **Tabler Icons**: pobierz paczkę SVG do `./assets/tabler-icons/` (np. wybrane pliki: `jar.svg`, `package.svg`, `tool.svg`).
* **Fonty**: wrzuć Inter (TTF/OTF) i Noto Color Emoji do `./assets/fonts/` (opcjonalnie – CairoSVG użyje systemowych jeśli są).

## Przykładowe wywołania

### Lista typów i arkuszy

```bash
curl http://localhost:8000/types
curl http://localhost:8000/sheets
```

### Pojedyncza etykieta (PDF)

```bash
curl -X POST http://localhost:8000/labels/single?fmt=pdf \
  -H 'content-type: application/json' \
  -d '{
    "type":"jar_label_small",
    "item": {"title":"Powidła śliwkowe","text":"2025 • bez cukru","icon":"jar"},
    "options": {"sheet":"A4","with_cut_marks":false,"bg":"#fff","color":"#111827","border":"#111827"}
  }' -o etykieta.pdf
```

### Paczka etykiet na arkusz A4 (PNG)

```bash
curl -X POST 'http://localhost:8000/labels/batch?fmt=png' \
  -H 'content-type: application/json' \
  -d '{
    "type":"jar_label_small",
    "items":[
      {"title":"Ogórki kiszone","text":"VIII 2025","icon":"jar"},
      {"title":"Dżem truskawkowy","text":"Bez cukru","icon":"jar"}
    ],
    "options":{"sheet":"L7160","with_cut_marks":true}
  }' -o arkusz.png
```

### Storage – tworzenie i druk braków

```bash
# utwórz spiżarnię
curl -X POST http://localhost:8000/storages -H 'content-type: application/json' -d '{"name":"Spiżarnia"}'
# dodaj etykiety (pożądana liczba sztuk)
curl -X POST http://localhost:8000/storages/1/labels -H 'content-type: application/json' -d '{
  "template_type":"jar_label_small","title":"Sos pomidorowy","text":"2025","icon":"jar","desired_qty":12
}'
# podgląd listy
curl http://localhost:8000/storages/1/labels
# wydrukuj brakujące
curl -X POST 'http://localhost:8000/storages/1/print-missing?fmt=pdf' -o braki.pdf
# oznacz, że wydrukowano 6 sztuk
curl -X POST 'http://localhost:8000/storages/1/labels/1/printed?qty=6'
```

## Konfiguracja

Zmienna `DATABASE_URL` (np. `postgresql+asyncpg://user:pass@postgres:5432/etykiety`) – domyślnie SQLite `local.db`.

## Docker

```bash
# build
docker build -t etykiety:0.1.0 .
# run (SQLite)
docker run --rm -p 8000:8000 -v $(pwd)/assets:/app/assets etykiety:0.1.0
```

## microk8s (lokalnie)

1. `microk8s enable dns storage`
2. `kubectl apply -f k8s/microk8s.yaml`
3. Po starcie: `kubectl port-forward svc/etykiety-svc 8000:80 -n etykiety`

> Manifest zawiera prosty Postgresa (do dev), PV hostPath oraz Deployment aplikacji.

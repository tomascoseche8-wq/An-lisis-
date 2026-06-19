#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update_scores.py — consulta la API de football-data.org y escribe
src/scores_live.json con todos los marcadores ya oficiales del
Mundial 2026. generate.py luego fusiona esos datos con el sitio.

Requiere la variable de entorno FOOTBALL_DATA_API_KEY.
Obtené tu clave gratuita en: https://www.football-data.org/client/register
(plan Free: 10 llamadas/min, suficiente para este uso)
"""
import os, sys, json, datetime, requests

BASE = os.path.dirname(__file__)
OUT  = os.path.join(BASE, "src", "scores_live.json")

# ── Mapeo nombre API → código de 3 letras usado en el sitio ──────────────────
# football-data.org usa nombres en inglés; incluimos variantes conocidas.
API_NAME_TO_CODE = {
    "Argentina": "ARG", "Spain": "ESP", "France": "FRA", "England": "ENG",
    "Portugal": "POR", "Brazil": "BRA", "Morocco": "MAR", "Netherlands": "NED",
    "Belgium": "BEL", "Germany": "GER", "Croatia": "CRO", "Colombia": "COL",
    "Mexico": "MEX", "Senegal": "SEN", "Uruguay": "URU",
    "United States": "USA", "USA": "USA",
    "Japan": "JPN", "Switzerland": "SUI", "Iran": "IRN",
    "Turkey": "TUR", "Türkiye": "TUR",
    "Ecuador": "ECU", "Austria": "AUT", "South Korea": "KOR",
    "Korea Republic": "KOR", "Australia": "AUS", "Algeria": "ALG",
    "Egypt": "EGY", "Canada": "CAN", "Norway": "NOR",
    "Ivory Coast": "CIV", "Côte d'Ivoire": "CIV", "Cote d'Ivoire": "CIV",
    "Panama": "PAN", "Sweden": "SWE", "Czechia": "CZE",
    "Czech Republic": "CZE", "Paraguay": "PAR", "Scotland": "SCO",
    "Tunisia": "TUN", "DR Congo": "COD", "Congo DR": "COD",
    "Democratic Republic of Congo": "COD",
    "Uzbekistan": "UZB", "Qatar": "QAT", "Iraq": "IRQ",
    "South Africa": "RSA", "Saudi Arabia": "KSA", "Jordan": "JOR",
    "Bosnia and Herzegovina": "BIH", "Bosnia & Herzegovina": "BIH",
    "Cape Verde": "CPV", "Ghana": "GHA",
    "Curaçao": "CUW", "Curacao": "CUW",
    "Haiti": "HAI", "New Zealand": "NZL",
}

STATUS_FINISHED = {"FINISHED", "FT", "AET", "PEN"}


def fetch_matches(api_key: str) -> list:
    """Devuelve la lista de partidos del Mundial 2026 desde la API."""
    url = "https://api.football-data.org/v4/competitions/WC/matches"
    headers = {"X-Auth-Token": api_key}
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json().get("matches", [])


def parse_scores(matches: list) -> dict:
    """
    Convierte la lista de partidos de la API al formato
    {(HOME_CODE, AWAY_CODE): (goles_home, goles_away)}.
    Solo incluye partidos con resultado oficial.
    """
    scores = {}
    for m in matches:
        status = m.get("status", "")
        if status not in STATUS_FINISHED:
            continue

        home_name = m.get("homeTeam", {}).get("name", "")
        away_name = m.get("awayTeam", {}).get("name", "")
        hc = API_NAME_TO_CODE.get(home_name)
        ac = API_NAME_TO_CODE.get(away_name)

        if not hc or not ac:
            print(f"  ⚠ Nombre desconocido: '{home_name}' o '{away_name}' — omitido")
            continue

        score = m.get("score", {})
        full  = score.get("fullTime", {})
        gh = full.get("home")
        ga = full.get("away")

        if gh is None or ga is None:
            continue

        scores[(hc, ac)] = (int(gh), int(ga))

    return scores


def save(scores: dict) -> None:
    """Guarda en src/scores_live.json (claves como strings 'HHH-AAA')."""
    serializable = {f"{h}-{a}": list(v) for (h, a), v in scores.items()}
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({
            "updated_at": datetime.datetime.utcnow().isoformat() + "Z",
            "scores": serializable,
        }, f, ensure_ascii=False, indent=2)
    print(f"✅ {len(scores)} resultados guardados en {OUT}")


def main():
    api_key = os.environ.get("FOOTBALL_DATA_API_KEY", "").strip()

    if not api_key:
        print("⚠ FOOTBALL_DATA_API_KEY no definida — omitiendo actualización de marcadores.")
        # Crear archivo vacío para que generate.py no falle
        if not os.path.exists(OUT):
            save({})
        return

    print(f"🔄 Consultando football-data.org ({datetime.datetime.utcnow().strftime('%H:%M UTC')})…")
    try:
        raw = fetch_matches(api_key)
        scores = parse_scores(raw)
        save(scores)
        print(f"   Partidos totales en la API: {len(raw)}")
        print(f"   Con resultado oficial: {len(scores)}")
    except requests.HTTPError as e:
        print(f"❌ Error HTTP {e.response.status_code}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

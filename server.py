"""
Damia - serveur local (intégré au programme, rien à installer côté utilisateur).
- Sert l'interface et le logo
- Garde la clé API dans le profil Windows de l'utilisateur (jamais dans l'interface)
- /api/transcribe : transcription du français
- /api/suggest    : rebond et question
- /api/summary    : résumé et courriel de suivi
"""
import json
import os
import sys
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory
from openai import OpenAI

from config_store import load_config, save_config

BASE_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
app = Flask(__name__)

TRANSCRIBE_MODEL = os.getenv("TRANSCRIBE_MODEL", "gpt-4o-mini-transcribe")
SUGGEST_MODEL = os.getenv("SUGGEST_MODEL", "gpt-5-mini")
SUMMARY_MODEL = os.getenv("SUMMARY_MODEL", "gpt-5-mini")

SUGGEST_PROMPT = """Tu aides un commercial pendant un appel de découverte, selon la méthode Sandler.
Règles :
- Réponds dans la langue indiquée dans le contexte (fr ou en).
- Ton chaleureux, souriant et respectueux. Jamais agressif, jamais de pression.
- Objectif : comprendre le problème avant de proposer une solution.
- "rebond" : UNE phrase courte qui relance sur le dernier propos (impact, exemple, décideurs ou budget selon l'étape).
- "question" : une question de découverte utile maintenant, sinon null.
- "alert" : un avertissement court si le budget n'est pas abordé alors que la douleur est confirmée, ou si on s'apprête à proposer une solution trop tôt. Sinon null.
Réponds uniquement en JSON avec exactement les clés "rebond", "question", "alert"."""

SUMMARY_PROMPT = """Tu rédiges, pour un commercial, le résumé d'un appel de découverte (méthode Sandler) et un courriel de suivi.
Règles :
- Résumé : douleur, impact, budget, décideurs, prochaines étapes. Mentionne "non abordé" si un point manque. Pas d'invention.
- Courriel : court (6 à 8 phrases), chaleureux, humain, en français (ou en anglais si le contexte l'indique). Un seul appel à l'action. Utilise [Prénom] et [Votre nom] comme placeholders.
Réponds uniquement en JSON avec exactement les clés "resume" et "mail"."""


def get_api_key() -> str:
    return os.getenv("OPENAI_API_KEY") or load_config().get("openai_api_key", "")


def get_client():
    key = get_api_key()
    return OpenAI(api_key=key) if key else None


@app.get("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")


@app.get("/logo.svg")
def logo():
    return send_from_directory(BASE_DIR, "logo.svg")


@app.get("/api/settings")
def get_settings():
    # La clé ne sort jamais du serveur : on renvoie seulement son état.
    return jsonify({"key_loaded": bool(get_api_key())})


@app.post("/api/settings")
def set_settings():
    key = ((request.get_json(silent=True) or {}).get("openai_api_key") or "").strip()
    if not key.startswith("sk-"):
        return jsonify({"error": "Clé invalide : elle doit commencer par sk-"}), 400
    config = load_config()
    config["openai_api_key"] = key
    save_config(config)
    return jsonify({"key_loaded": True})


@app.post("/api/transcribe")
def transcribe():
    client = get_client()
    if client is None:
        return jsonify({"error": "no_key"}), 400
    audio = request.files.get("audio")
    if audio is None:
        return jsonify({"error": "Fichier audio manquant"}), 400
    try:
        result = client.audio.transcriptions.create(
            model=TRANSCRIBE_MODEL,
            file=(audio.filename or "segment.webm", audio.stream, audio.mimetype or "audio/webm"),
            language="fr",
        )
        return jsonify({"text": result.text})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 502


@app.post("/api/suggest")
def suggest():
    client = get_client()
    if client is None:
        return jsonify({"error": "no_key"}), 400
    data = request.get_json(silent=True) or {}
    user_msg = (
        f"Contexte de l'appel :\n{json.dumps(data.get('context', {}), ensure_ascii=False)}\n\n"
        f"Étape Sandler en cours : {data.get('step', 'inconnue')}\n\n"
        f"Dernier passage de la conversation :\n{data.get('transcript', '')}"
    )
    try:
        completion = client.chat.completions.create(
            model=SUGGEST_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SUGGEST_PROMPT},
                {"role": "user", "content": user_msg},
            ],
        )
        return jsonify(json.loads(completion.choices[0].message.content))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 502


@app.post("/api/summary")
def summary():
    client = get_client()
    if client is None:
        return jsonify({"error": "no_key"}), 400
    data = request.get_json(silent=True) or {}
    user_msg = (
        f"Contexte de l'appel :\n{json.dumps(data.get('context', {}), ensure_ascii=False)}\n\n"
        f"Transcription complète :\n{data.get('transcript', '')}"
    )
    try:
        completion = client.chat.completions.create(
            model=SUMMARY_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SUMMARY_PROMPT},
                {"role": "user", "content": user_msg},
            ],
        )
        return jsonify(json.loads(completion.choices[0].message.content))
    except Exception as exc:
        return jsonify({"error": str(exc)}), 502

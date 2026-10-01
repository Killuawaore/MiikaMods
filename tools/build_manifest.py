#!/usr/bin/env python3
import base64
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from cryptography.hazmat.primitives import serialization

ROOT = Path(__file__).resolve().parents[1]
USERS_FILE = ROOT / "access" / "usuarios.txt"
MANIFEST_FILE = ROOT / "access" / "manifest.json"
PUBLIC_KEY_FILE = ROOT / "access" / "public-key.txt"
NAME_RE = re.compile(r"^[A-Za-z0-9_]{3,16}$")


def load_names():
    names = []
    seen = set()
    for raw in USERS_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if not NAME_RE.fullmatch(line):
            raise SystemExit(f"Nick invalido em access/usuarios.txt: {line!r}")
        key = line.lower()
        if key in seen:
            continue
        seen.add(key)
        names.append(line)
    return names


def previous_users():
    if not MANIFEST_FILE.is_file():
        return {}
    try:
        envelope = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
        payload = json.loads(base64.b64decode(envelope["payload"]).decode("utf-8"))
        return {
            entry["name"].lower(): entry["uuid"]
            for entry in payload.get("users", [])
            if isinstance(entry, dict) and entry.get("name") and entry.get("uuid")
        }
    except Exception:
        return {}


def resolve_uuid(name):
    encoded = urllib.parse.quote(name)
    urls = [
        "https://api.minecraftservices.com/minecraft/profile/lookup/name/" + encoded,
        "https://api.mojang.com/users/profiles/minecraft/" + encoded,
    ]
    last_error = None

    for url in urls:
        req = urllib.request.Request(url, headers={"User-Agent": "Miika-Runtime-Manifest/1"})
        try:
            with urllib.request.urlopen(req, timeout=12) as response:
                data = json.loads(response.read().decode("utf-8"))
            uuid = str(data.get("id", "")).replace("-", "").lower()
            if re.fullmatch(r"[0-9a-f]{32}", uuid):
                canonical = str(data.get("name") or name)
                return canonical, uuid
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError) as exc:
            last_error = exc

    raise SystemExit(f"Conta Minecraft nao encontrada: {name}. Ultimo erro: {last_error}")


def load_private_key():
    encoded = os.environ.get("RUNTIME_PROFILE_KEY", "").strip()
    if not encoded:
        raise SystemExit("GitHub Secret RUNTIME_PROFILE_KEY nao foi configurado.")
    try:
        raw = base64.b64decode(encoded, validate=True)
        key = serialization.load_der_private_key(raw, password=None)
    except Exception as exc:
        raise SystemExit("RUNTIME_PROFILE_KEY invalida.") from exc

    expected = PUBLIC_KEY_FILE.read_text(encoding="utf-8").strip()
    actual = base64.b64encode(
        key.public_key().public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    ).decode("ascii")
    if actual != expected:
        raise SystemExit("A chave privada do Secret nao combina com access/public-key.txt.")
    return key


def main():
    names = load_names()
    previous = previous_users()
    users = []

    for name in names:
        old_uuid = previous.get(name.lower())
        if old_uuid and re.fullmatch(r"[0-9a-f]{32}", old_uuid):
            users.append({"name": name, "uuid": old_uuid})
            continue
        canonical, uuid = resolve_uuid(name)
        users.append({"name": canonical, "uuid": uuid})

    users.sort(key=lambda entry: (entry["name"].lower(), entry["uuid"]))
    payload_obj = {
        "version": 1,
        "issued_at": int(time.time()),
        "users": users,
    }
    payload = json.dumps(payload_obj, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    signature = load_private_key().sign(payload)
    envelope = {
        "payload": base64.b64encode(payload).decode("ascii"),
        "signature": base64.b64encode(signature).decode("ascii"),
    }
    MANIFEST_FILE.write_text(
        json.dumps(envelope, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(f"Manifesto gerado para {len(users)} usuario(s).")


if __name__ == "__main__":
    main()

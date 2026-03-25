# 🤖 Dreame Vacuum MCP — Setup Guide

---

## 1. Run setup.sh

```sh
sh setup.sh
```

This will:
- Install **HACS v2.0.5** into `config/custom_components/hacs`
- Start **Home Assistant** via `docker compose up --build -d`

> ⚠️ Copying files on a Windows-mounted filesystem is slow (~2 min). The script shows progress — it's not frozen.

---

## 2. Configure Home Assistant

Open **http://localhost:8123** (wait ~60s after setup.sh).

Complete the wizard, then:

1. **Activate HACS**: Settings → Devices & Services → Add Integration → HACS → authorize with GitHub
2. **Install dreame-vacuum**: HACS → Integrations → search `Dreame Vacuum` → download the latest version (⚠️use a **beta release** if your model is recent) → restart HA
3. **Add robot**: Settings → Devices & Services → Add Integration → Dreame Vacuum → login with **DreameHome** credentials → select your robot

---

## 3. Get your tokens

**HA Long-Lived Token:**
Profile (bottom left) → Security → Long-Lived Access Tokens → Create Token → copy it immediately

**Entity ID:**
Developer Tools → States → filter `vacuum.` → copy your entity id (e.g. `vacuum.mochi`)

---

## 4. Create .env file

In the project folder create a `.env` file:

```
TOKEN=eyJ0eXAiOiJKV1...
ENTITY_ID=vacuum.your_robot
```

> ⚠️ Never commit `.env` to Git — add it to `.gitignore`

---

## 5. Test

```sh
docker compose run --rm dreame-python-client python src/main.py list_rooms
```

Expected output:
```
🗺️  Map: Home
  ID 1: Living Room
  ID 2: Kitchen
  ID 3: Bedroom
```
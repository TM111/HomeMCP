#!/bin/sh
# ============================================================
# setup.sh — Installa HACS e avvia Home Assistant
# Uso: sh setup.sh
# ============================================================

# ─── Versione pinned ─────────────────────────────────────────
HACS_VERSION="2.0.5"

CONFIG_DIR="$(pwd)/config"
HACS_DIR="$CONFIG_DIR/custom_components/hacs"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║         Setup HACS per Home Assistant    ║"
echo "╚══════════════════════════════════════════╝"
echo "   HACS: v$HACS_VERSION"
echo ""

# ─── Verifica dipendenze ─────────────────────────────────────
for cmd in curl unzip docker; do
  if ! command -v $cmd > /dev/null 2>&1; then
    echo "❌ '$cmd' non trovato. Installalo prima di continuare."
    exit 1
  fi
done
echo "✅ Dipendenze OK (curl, unzip, docker)"

# ─── Crea cartelle ───────────────────────────────────────────
mkdir -p "$HACS_DIR"
echo "✅ Cartelle create"

# ─── Funzione copia con progress ─────────────────────────────
copy_with_progress() {
  SRC="$1"
  DEST="$2"
  TOTAL=$(find "$SRC" -type f | wc -l)
  COUNT=0
  find "$SRC" -type f | while read -r file; do
    rel="${file#$SRC/}"
    dir=$(dirname "$DEST/$rel")
    mkdir -p "$dir"
    cp "$file" "$DEST/$rel"
    COUNT=$((COUNT + 1))
    PCT=$((COUNT * 100 / TOTAL))
    printf "\r   → Copia: %d%% (%d/%d file)" "$PCT" "$COUNT" "$TOTAL"
  done
  echo ""
}

# ─── Installa HACS ───────────────────────────────────────────
echo ""
echo "📦 Download HACS v$HACS_VERSION..."
curl -L --progress-bar \
  "https://github.com/hacs/integration/releases/download/${HACS_VERSION}/hacs.zip" \
  -o /tmp/hacs.zip

echo "   → Estrazione in /tmp..."
TMP_HACS="/tmp/hacs_extract"
rm -rf "$TMP_HACS" && mkdir -p "$TMP_HACS"
unzip -qo /tmp/hacs.zip -d "$TMP_HACS"
rm /tmp/hacs.zip

copy_with_progress "$TMP_HACS" "$HACS_DIR"
rm -rf "$TMP_HACS"
echo "✅ HACS v$HACS_VERSION installato"

# ─── Avvia Docker Compose ─────────────────────────────────────
echo ""
echo "🐳 Build e avvio Home Assistant..."
docker compose up --build -d

echo ""
echo "════════════════════════════════════════════"
echo "✅ Setup completato!"
echo ""
echo "Prossimi passi:"
echo "  1. Apri http://localhost:8123"
echo "  2. Completa il wizard HA (crea utente admin)"
echo "  3. Settings → Devices & Services → Add Integration → HACS"
echo "     (autorizza con GitHub — obbligatorio una volta)"
echo "  4. In HACS cerca 'Dreame Vacuum' e installalo"
echo "  5. Settings → Devices & Services → Add Integration → Dreame Vacuum"
echo "     (inserisci le credenziali DreameHome)"
echo "════════════════════════════════════════════"
echo ""
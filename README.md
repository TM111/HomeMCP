# HomeMCP - Smart Home Assistant

Orchestratore modulare per la smart home: un LLM locale (Ollama) che utilizza moduli MCP per controllare dispositivi.

## Architettura

```
┌─────────────────────────────────────────────┐
│  Orchestrator (Ollama + qwen2.5:7b)         │
│  - Chat interattiva                         │
│  - Tool calling verso i moduli MCP          │
└───────┬─────────────────────┬───────────────┘
        │                     │
   ┌────▼─────┐         ┌────▼─────┐
   │ Dreame   │         │ Futuro   │
   │ MCP :6278│         │ modulo   │
   └──────────┘         └──────────┘
```

## Quick Start

### 1. Avvia il modulo Dreame (aspirapolvere)

```bash
cd dreame
# Configura dreame/.env con TOKEN, ENTITY_ID, HA_URL
docker compose up -d
```

### 2. Avvia l'orchestratore + Ollama

```bash
# Dalla cartella principale
docker compose up -d          # avvia Ollama
docker compose run orchestrator  # avvia la chat interattiva
```

Al primo avvio, il modello `qwen2.5:7b` verrà scaricato automaticamente (~4.7 GB).

### 3. Chatta

```
You: Pulisci il salotto
  [tool] vacuum_list_rooms({})
  [result] {1: "Salotto", 2: "Camera", ...}
  [tool] vacuum_clean_rooms({"room_ids": [1]})
  [result] Cleaning started for rooms [1] (repeats=1)
Assistant: Ho avviato la pulizia del salotto!
```

## Aggiungere un nuovo modulo

1. Crea una cartella per il modulo (es. `lights/`) con il suo `docker-compose.yml` e server MCP
2. Esponi il server MCP su una porta (es. `:6279`)
3. Aggiungi il server in `orchestrator/config/mcp_servers.json`:

```json
{
  "mcp_servers": [
    { "name": "dreame-vacuum", "url": "http://host.docker.internal:6278/sse" },
    { "name": "lights",        "url": "http://host.docker.internal:6279/sse" }
  ]
}
```

4. Riavvia l'orchestratore: `docker compose run orchestrator`

## GPU (opzionale)

Per abilitare la GPU NVIDIA per Ollama, decommenta la sezione `deploy` nel `docker-compose.yml` principale.
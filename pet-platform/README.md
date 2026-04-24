# AXIS — Industrial Digital Twin Platform

Build-ready scaffold for a PET bottle plant digital twin platform.
Companion to `SPEC.md` (master specification) and `../pet-DT.html` (single-file interactive demo).

## Structure

```
pet-platform/
├─ SPEC.md                    Full product + arch + UX + roadmap spec
├─ README.md                  This file
├─ docker-compose.yml         Local dev stack (postgres+timescale, redis, kafka)
├─ frontend/                  React + Vite + three.js (React Three Fiber)
│  ├─ package.json
│  ├─ vite.config.ts
│  ├─ index.html
│  └─ src/
│     ├─ main.tsx
│     ├─ App.tsx
│     ├─ pages/
│     │  ├─ Dashboard.tsx
│     │  ├─ Twin.tsx
│     │  ├─ Assets.tsx
│     │  ├─ Maintenance.tsx
│     │  ├─ Simulation.tsx
│     │  └─ Copilot.tsx
│     ├─ scene/
│     │  ├─ Viewer.tsx            R3F Canvas + streaming loader
│     │  ├─ AssetNode.tsx         glTF mesh + picking + tooltip
│     │  ├─ SensorSprite.tsx      IoT overlay billboard
│     │  └─ TileLoader.ts         3DTiles-inspired chunk loader
│     ├─ state/
│     │  ├─ assets.ts             zustand store
│     │  ├─ telemetry.ts          ws stream
│     │  └─ selection.ts          valtio proxy
│     └─ api/
│        ├─ client.ts             fetch + zod
│        └─ ws.ts                 WebSocket telemetry
├─ backend/                   FastAPI + modular monolith
│  ├─ pyproject.toml
│  ├─ alembic.ini
│  └─ app/
│     ├─ main.py
│     ├─ settings.py
│     ├─ db.py
│     ├─ modules/
│     │  ├─ assets/            (schema, service, router)
│     │  ├─ telemetry/
│     │  ├─ work_orders/
│     │  ├─ documents/
│     │  ├─ simulation/
│     │  └─ copilot/
│     └─ adapters/
│        ├─ sap_mock.py
│        ├─ maximo_mock.py
│        └─ mqtt_ingest.py
└─ edge/                      Edge agent (Rust — skeleton only)
   └─ README.md
```

## Quick start

```bash
# 1. Backend
cd backend
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload

# 2. Frontend
cd ../frontend
npm install
npm run dev  # http://localhost:5173

# 3. Mocks running on :8000 emit fake telemetry and expose SAP/Maximo endpoints
```

## Demo commercial

Para la **reunión de cliente**, abre `../pet-DT.html` directamente en Chrome o vía:

```
python -m http.server --directory ..
open http://localhost:8000/pet-DT.html
```

Es una pieza standalone, sin instalación, diseñada para impresionar en 60 segundos.

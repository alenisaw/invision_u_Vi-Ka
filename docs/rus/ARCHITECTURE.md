# РђСЂС…РёС‚РµРєС‚СѓСЂР° СЃРёСЃС‚РµРјС‹

---

## РЎС‚СЂСѓРєС‚СѓСЂР° РґРѕРєСѓРјРµРЅС‚Р°

- [РћР±Р·РѕСЂ СЃРёСЃС‚РµРјС‹](#РѕР±Р·РѕСЂ-СЃРёСЃС‚РµРјС‹)
- [Р”РёР°РіСЂР°РјРјР° 1. РЎРєРІРѕР·РЅРѕР№ flow РїРѕ СЌС‚Р°РїР°Рј](#РґРёР°РіСЂР°РјРјР°-1-СЃРєРІРѕР·РЅРѕР№-flow-РїРѕ-СЌС‚Р°РїР°Рј)
- [РђСЂС…РёС‚РµРєС‚СѓСЂРЅС‹Рµ РїСЂРёРЅС†РёРїС‹](#Р°СЂС…РёС‚РµРєС‚СѓСЂРЅС‹Рµ-РїСЂРёРЅС†РёРїС‹)
- [Р­С‚Р°РїС‹ runtime](#СЌС‚Р°РїС‹-runtime)
- [РљР°СЂС‚Р° РїСѓР±Р»РёС‡РЅС‹С… РЅР°Р·РІР°РЅРёР№](#РєР°СЂС‚Р°-РїСѓР±Р»РёС‡РЅС‹С…-РЅР°Р·РІР°РЅРёР№)
- [РњРѕРґРµР»СЊ СѓРїСЂР°РІР»РµРЅРёСЏ РґР°РЅРЅС‹РјРё](#РјРѕРґРµР»СЊ-СѓРїСЂР°РІР»РµРЅРёСЏ-РґР°РЅРЅС‹РјРё)
- [Р”РёР°РіСЂР°РјРјР° 2. РЎР»РѕРё СЂР°Р·РґРµР»РµРЅРёСЏ РґР°РЅРЅС‹С…](#РґРёР°РіСЂР°РјРјР°-2-СЃР»РѕРё-СЂР°Р·РґРµР»РµРЅРёСЏ-РґР°РЅРЅС‹С…)
- [Р”РёР°РіСЂР°РјРјР° 3. Workflow РєРѕРјРёСЃСЃРёРё](#РґРёР°РіСЂР°РјРјР°-3-workflow-РєРѕРјРёСЃСЃРёРё)
- [Р”РёР°РіСЂР°РјРјР° 4. Frontend Рё API surface](#РґРёР°РіСЂР°РјРјР°-4-frontend-Рё-api-surface)
- [РЎС‚СЂСѓРєС‚СѓСЂР° СЂРµРїРѕР·РёС‚РѕСЂРёСЏ](#СЃС‚СЂСѓРєС‚СѓСЂР°-СЂРµРїРѕР·РёС‚РѕСЂРёСЏ)

---

## РћР±Р·РѕСЂ СЃРёСЃС‚РµРјС‹

РџР»Р°С‚С„РѕСЂРјР° inVision U РґР»СЏ РїСЂРёРµРјРЅРѕР№ РєРѕРјРёСЃСЃРёРё РїСЂРµРґСЃС‚Р°РІР»СЏРµС‚ СЃРѕР±РѕР№ РјРѕРґСѓР»СЊРЅС‹Р№ РјРѕРЅРѕР»РёС‚ РґР»СЏ РїРѕРґРґРµСЂР¶РєРё СЂРµС€РµРЅРёР№ РїРѕ РєР°РЅРґРёРґР°С‚Р°Рј. Р’ СЂРµРїРѕР·РёС‚РѕСЂРёРё РЅР°С…РѕРґСЏС‚СЃСЏ Рё FastAPI backend, Рё Next.js workspace РєРѕРјРёСЃСЃРёРё.

РўРµРєСѓС‰РёР№ runtime СЂР°Р±РѕС‚Р°РµС‚ РєР°Рє СЃРёРЅС…СЂРѕРЅРЅС‹Р№ request-response pipeline:

- РІС…РѕРґРЅС‹Рµ РґР°РЅРЅС‹Рµ РєР°РЅРґРёРґР°С‚Р° РїРѕСЃС‚СѓРїР°СЋС‚ С‡РµСЂРµР· СЌС‚Р°Рї intake РёР»Рё С‡РµСЂРµР· РїРѕР»РЅС‹Р№ pipeline gateway
- `ASR` Р·Р°РїСѓСЃРєР°РµС‚СЃСЏ, РµСЃР»Рё Сѓ РєР°РЅРґРёРґР°С‚Р° РµСЃС‚СЊ РїСѓР±Р»РёС‡РЅРѕРµ Р°СѓРґРёРѕ РёР»Рё РІРёРґРµРѕ
- `Privacy` РѕС‚РґРµР»СЏРµС‚ PII РґРѕ Р»СЋР±РѕР№ model-facing РѕР±СЂР°Р±РѕС‚РєРё
- `Profile`, `Extraction`, `AI Detect`, `Scoring` Рё `Explanation` С„РѕСЂРјРёСЂСѓСЋС‚ Р°РЅР°Р»РёС‚РёС‡РµСЃРєРѕРµ РїСЂРµРґСЃС‚Р°РІР»РµРЅРёРµ
- `Review` РѕР±СЃР»СѓР¶РёРІР°РµС‚ РґРµР№СЃС‚РІРёСЏ РєРѕРјРёСЃСЃРёРё, РёС‚РѕРіРѕРІРѕРµ СЂРµС€РµРЅРёРµ РїСЂРµРґСЃРµРґР°С‚РµР»СЏ Рё Р¶СѓСЂРЅР°Р»
- РІСЃРµ СЃРѕСЃС‚РѕСЏРЅРёСЏ СЃРѕС…СЂР°РЅСЏСЋС‚СЃСЏ РІ PostgreSQL

РџР»Р°С‚С„РѕСЂРјР° РѕСЃС‚Р°РµС‚СЃСЏ human-in-the-loop:

- РЅРµ РїСЂРёРЅРёРјР°РµС‚ Р°РІС‚РѕРЅРѕРјРЅРѕРµ С„РёРЅР°Р»СЊРЅРѕРµ СЂРµС€РµРЅРёРµ Рѕ Р·Р°С‡РёСЃР»РµРЅРёРё
- РїРѕРєР°Р·С‹РІР°РµС‚ confidence, evidence Рё caution-СЃРёРіРЅР°Р»С‹
- РЅРµ РѕС‚РїСЂР°РІР»СЏРµС‚ С‡СѓРІСЃС‚РІРёС‚РµР»СЊРЅС‹Рµ РґР°РЅРЅС‹Рµ РІ Р°РЅР°Р»РёС‚РёС‡РµСЃРєРёРµ СЌС‚Р°РїС‹
- Р»РѕРіРёСЂСѓРµС‚ РґРµР№СЃС‚РІРёСЏ РєРѕРјРёСЃСЃРёРё Рё РёС‚РѕРіРѕРІС‹Рµ СЂРµС€РµРЅРёСЏ

---

## Р”РёР°РіСЂР°РјРјР° 1. РЎРєРІРѕР·РЅРѕР№ flow РїРѕ СЌС‚Р°РїР°Рј

```mermaid
flowchart LR
    subgraph InputLayer["РЎР»РѕР№ РІС…РѕРґР°"]
        Candidate["РџРѕРґР°С‡Р° РєР°РЅРґРёРґР°С‚Р°"]
        Demo["Р”РµРјРѕ-СЃС†РµРЅР°СЂРёР№"]
        Gateway["Gateway"]
        Intake["Input Intake"]
    end

    subgraph ProcessingLayer["РЎР»РѕР№ РѕР±СЂР°Р±РѕС‚РєРё"]
        ASR["ASR"]
        Privacy["Privacy"]
        Profile["Profile"]
        Extraction["Extraction"]
        AIDetect["AI Detect"]
        Scoring["Scoring"]
        Explanation["Explanation"]
    end

    subgraph DecisionLayer["РЎР»РѕР№ СЂРµС€РµРЅРёР№"]
        Workspace["Workspace РєРѕРјРёСЃСЃРёРё"]
        Review["Review"]
    end

    subgraph StorageLayer["РЎР»РѕР№ С…СЂР°РЅРµРЅРёСЏ"]
        DB["PostgreSQL"]
    end

    Candidate --> Gateway
    Demo --> Gateway
    Gateway --> Intake
    Intake --> ASR
    Intake --> Privacy
    ASR --> Privacy
    Privacy --> Profile
    Profile --> Extraction
    Extraction --> AIDetect
    Extraction --> Scoring
    AIDetect -. РґРѕРїРѕР»РЅРёС‚РµР»СЊРЅС‹Рµ СЃРёРіРЅР°Р»С‹ .-> Scoring
    Scoring --> Explanation
    Explanation --> Workspace
    Workspace --> Review

    Intake -. СЃРѕС…СЂР°РЅРµРЅРёРµ .-> DB
    Privacy -. СЃРѕС…СЂР°РЅРµРЅРёРµ .-> DB
    Profile -. СЃРѕС…СЂР°РЅРµРЅРёРµ .-> DB
    Extraction -. СЃРѕС…СЂР°РЅРµРЅРёРµ .-> DB
    Scoring -. СЃРѕС…СЂР°РЅРµРЅРёРµ .-> DB
    Explanation -. СЃРѕС…СЂР°РЅРµРЅРёРµ .-> DB
    Review -. СЃРѕС…СЂР°РЅРµРЅРёРµ .-> DB

    style InputLayer fill:transparent,stroke:#7d7d7d,stroke-dasharray: 5 5
    style ProcessingLayer fill:transparent,stroke:#7d7d7d,stroke-dasharray: 5 5
    style DecisionLayer fill:transparent,stroke:#7d7d7d,stroke-dasharray: 5 5
    style StorageLayer fill:transparent,stroke:#7d7d7d,stroke-dasharray: 5 5
```

---

## РђСЂС…РёС‚РµРєС‚СѓСЂРЅС‹Рµ РїСЂРёРЅС†РёРїС‹

### Privacy by Design

PII РёР·РѕР»РёСЂСѓРµС‚СЃСЏ РґРѕ Р»СЋР±РѕР№ model-facing РѕР±СЂР°Р±РѕС‚РєРё. AI Рё ML СЌС‚Р°РїС‹ СЂР°Р±РѕС‚Р°СЋС‚ С‚РѕР»СЊРєРѕ СЃ Р±РµР·РѕРїР°СЃРЅС‹Рј РєРѕРЅС‚РµРЅС‚РѕРј Рё СЂР°Р·СЂРµС€РµРЅРЅС‹РјРё operational metadata.

### Explainability First

РЎРєРѕСЂРёРЅРі РґРѕР»Р¶РµРЅ РѕСЃС‚Р°РІР°С‚СЊСЃСЏ СЂР°Р·Р±РѕСЂРЅС‹Рј РґР»СЏ РєРѕРјРёСЃСЃРёРё. РРЅС‚РµСЂС„РµР№СЃ РїРѕРєР°Р·С‹РІР°РµС‚ С„Р°РєС‚РѕСЂРЅС‹Рµ Р±Р»РѕРєРё, caution-РјР°СЂРєРµСЂС‹, evidence Рё РёС‚РѕРіРѕРІС‹Рµ РѕР±СЉСЏСЃРЅРµРЅРёСЏ, Р° РЅРµ РѕРґРёРЅ РЅРµРїСЂРѕР·СЂР°С‡РЅС‹Р№ Р±Р°Р»Р».

### Human in the Loop

Р РµРєРѕРјРµРЅРґР°С†РёРё РЅРѕСЃСЏС‚ advisory-С…Р°СЂР°РєС‚РµСЂ. Р¤РёРЅР°Р»СЊРЅРѕРµ РґРІРёР¶РµРЅРёРµ РїРѕ РєР°РЅРґРёРґР°С‚Сѓ РѕСЃС‚Р°РµС‚СЃСЏ РІРЅСѓС‚СЂРё workflow РєРѕРјРёСЃСЃРёРё, РіРґРµ РѕС‚РґРµР»СЊРЅРѕ С„РёРєСЃРёСЂСѓСЋС‚СЃСЏ СЂРµРєРѕРјРµРЅРґР°С†РёРё С‡Р»РµРЅРѕРІ РєРѕРјРёСЃСЃРёРё Рё СЂРµС€РµРЅРёРµ РїСЂРµРґСЃРµРґР°С‚РµР»СЏ.

### Session Auth Рё RBAC

Р—Р°С‰РёС‰РµРЅРЅС‹Рµ РјР°СЂС€СЂСѓС‚С‹ РёСЃРїРѕР»СЊР·СѓСЋС‚ HTTP-only session cookie Рё backend RBAC РґР»СЏ СЂРѕР»РµР№ `admin`, `chair` Рё `reviewer`.

### РЎРёРЅС…СЂРѕРЅРЅС‹Р№ Р±Р°Р·РѕРІС‹Р№ pipeline

РћСЃРЅРѕРІРЅРѕР№ Р»РѕРєР°Р»СЊРЅС‹Р№ СЃС‚РµРє СЂР°Р±РѕС‚Р°РµС‚ РєР°Рє СЃРёРЅС…СЂРѕРЅРЅР°СЏ РѕСЂРєРµСЃС‚СЂР°С†РёСЏ РІРЅСѓС‚СЂРё API-РїСЂРѕС†РµСЃСЃР°. Р”Р»СЏ Р±Р°Р·РѕРІРѕРіРѕ review workflow РѕС‚РґРµР»СЊРЅС‹Р№ worker-СЃР»РѕР№ РЅРµ РѕР±СЏР·Р°С‚РµР»РµРЅ.

---

## Р­С‚Р°РїС‹ runtime

### Gateway

РџСѓР±Р»РёС‡РЅР°СЏ РІС…РѕРґРЅР°СЏ С‚РѕС‡РєР° API Рё СЃР»РѕР№ orchestration РґР»СЏ СЃРёРЅС…СЂРѕРЅРЅРѕРіРѕ pipeline, batch-Р·Р°РїСѓСЃРєРѕРІ Рё committee-facing backend routes.

### Input Intake

Р­С‚Р°Рї РІС…РѕРґРЅС‹С… РґР°РЅРЅС‹С… РІР°Р»РёРґРёСЂСѓРµС‚ payload РєР°РЅРґРёРґР°С‚Р°, СЃС‡РёС‚Р°РµС‚ РЅР°С‡Р°Р»СЊРЅСѓСЋ Р·Р°РїРѕР»РЅРµРЅРЅРѕСЃС‚СЊ Рё СЃРѕР·РґР°РµС‚ Р±Р°Р·РѕРІСѓСЋ Р·Р°РїРёСЃСЊ РєР°РЅРґРёРґР°С‚Р°. Р’ РїСѓР±Р»РёС‡РЅРѕР№ РґРѕРєСѓРјРµРЅС‚Р°С†РёРё СЌС‚Рѕ РѕРїРёСЃС‹РІР°РµС‚СЃСЏ РєР°Рє СЌС‚Р°Рї intake, Р° РЅРµ РєР°Рє РѕС‚РґРµР»СЊРЅС‹Р№ Р°РЅР°Р»РёС‚РёС‡РµСЃРєРёР№ РјРѕРґСѓР»СЊ.

### ASR

РџСЂРµРѕР±СЂР°Р·СѓРµС‚ РїСѓР±Р»РёС‡РЅС‹Рµ Р°СѓРґРёРѕ- Рё РІРёРґРµРѕРјР°С‚РµСЂРёР°Р»С‹ РєР°РЅРґРёРґР°С‚Р° РІ С‚СЂР°РЅСЃРєСЂРёРїС‚ Рё РјРµС‚Р°РґР°РЅРЅС‹Рµ РєР°С‡РµСЃС‚РІР° С‚СЂР°РЅСЃРєСЂРёРїС†РёРё.

### Privacy

Р Р°Р·РґРµР»СЏРµС‚ Р·Р°РїРёСЃСЊ РєР°РЅРґРёРґР°С‚Р° РЅР° PII, operational metadata Рё Р±РµР·РѕРїР°СЃРЅС‹Р№ Р°РЅР°Р»РёС‚РёС‡РµСЃРєРёР№ РєРѕРЅС‚РµРЅС‚.

### Profile

РЎРѕР±РёСЂР°РµС‚ РєР°РЅРѕРЅРёС‡РµСЃРєРёР№ РїСЂРѕС„РёР»СЊ РєР°РЅРґРёРґР°С‚Р° РёР· operational Рё safe СЃР»РѕРµРІ.

### Extraction

РР·РІР»РµРєР°РµС‚ СЃС‚СЂСѓРєС‚СѓСЂРёСЂРѕРІР°РЅРЅС‹Рµ decision signals РёР· Р±РµР·РѕРїР°СЃРЅРѕРіРѕ С‚РµРєСЃС‚Р°, С‚СЂР°РЅСЃРєСЂРёРїС‚Р° Рё СЃРІСЏР·Р°РЅРЅС‹С… evidence.

### AI Detect

Р”РѕР±Р°РІР»СЏРµС‚ РґРѕРїРѕР»РЅРёС‚РµР»СЊРЅС‹Рµ СЃРёРіРЅР°Р»С‹ РїРѕРґР»РёРЅРЅРѕСЃС‚Рё Рё AI-assisted-writing СЂРёСЃРєР°. Р­С‚Рё СЃРёРіРЅР°Р»С‹ РЅРµ Р·Р°РјРµРЅСЏСЋС‚ СЂРµС€РµРЅРёРµ РєРѕРјРёСЃСЃРёРё Рё СЂР°Р±РѕС‚Р°СЋС‚ РєР°Рє caution-input РґР»СЏ scoring Рё explanation.

### Scoring

РЎС‡РёС‚Р°РµС‚ РѕС†РµРЅРєСѓ РєР°РЅРґРёРґР°С‚Р°, confidence, ranking, recommendation category Рё review routing.

### Explanation

РџСЂРµРѕР±СЂР°Р·СѓРµС‚ score Рё evidence РІ reviewer-facing narrative, factor blocks Рё caution summaries.

### Review

РћР±СЃР»СѓР¶РёРІР°РµС‚ СЂР°Р±РѕС‡РёРµ РїСЂРѕСЃС‚СЂР°РЅСЃС‚РІР° РєР°РЅРґРёРґР°С‚РѕРІ, СЂРµРєРѕРјРµРЅРґР°С†РёРё РєРѕРјРёСЃСЃРёРё, РёС‚РѕРіРѕРІРѕРµ СЂРµС€РµРЅРёРµ РїСЂРµРґСЃРµРґР°С‚РµР»СЏ Рё Р¶СѓСЂРЅР°Р» РґРµР№СЃС‚РІРёР№.

### Storage

РЎРѕС…СЂР°РЅСЏРµС‚ СЃР»РѕРё РєР°РЅРґРёРґР°С‚Р°, РїСЂРѕРµРєС†РёРё, score-СЂРµР·СѓР»СЊС‚Р°С‚С‹, explanation-СЂРµР·СѓР»СЊС‚Р°С‚С‹ Рё СЃРѕР±С‹С‚РёСЏ РєРѕРјРёСЃСЃРёРё.

---

## РљР°СЂС‚Р° РїСѓР±Р»РёС‡РЅС‹С… РЅР°Р·РІР°РЅРёР№

Р”РѕРєСѓРјРµРЅС‚Р°С†РёСЏ РёСЃРїРѕР»СЊР·СѓРµС‚ РїСѓР±Р»РёС‡РЅС‹Рµ РЅР°Р·РІР°РЅРёСЏ СЌС‚Р°РїРѕРІ. РўРµРєСѓС‰РµРµ СЃРѕРѕС‚РІРµС‚СЃС‚РІРёРµ РїР°РєРµС‚Р°Рј РєРѕРґР°:

| РџСѓР±Р»РёС‡РЅРѕРµ РЅР°Р·РІР°РЅРёРµ | РўРµРєСѓС‰РёР№ РїР°РєРµС‚ |
|---|---|
| `Gateway` | `backend/app/modules/gateway` |
| `Input Intake` | `backend/app/modules/intake` |
| `ASR` | `backend/app/modules/asr` |
| `Privacy` | `backend/app/modules/privacy` |
| `Profile` | `backend/app/modules/profile` |
| `Extraction` | `backend/app/modules/extraction` |
| `AI Detect` | `backend/app/modules/extraction/ai_detector.py` |
| `Scoring` | `backend/app/modules/scoring` |
| `Explanation` | `backend/app/modules/explanation` |
| `Review` | `backend/app/modules/workspace` Рё `backend/app/modules/review` |
| `Storage` | `backend/app/modules/storage` |
| `Demo Layer` | `backend/app/modules/demo` |

---

## РњРѕРґРµР»СЊ СѓРїСЂР°РІР»РµРЅРёСЏ РґР°РЅРЅС‹РјРё

### Layer 1: Secure PII

РЎРѕРґРµСЂР¶РёС‚ Р·Р°С€РёС„СЂРѕРІР°РЅРЅС‹Рµ РёР»Рё Р·Р°С‰РёС‰РµРЅРЅС‹Рµ identity-РґР°РЅРЅС‹Рµ: СЋСЂРёРґРёС‡РµСЃРєРѕРµ РёРјСЏ, РєРѕРЅС‚Р°РєС‚С‹, Р°РґСЂРµСЃР°, СЃРІРµРґРµРЅРёСЏ Рѕ РґРѕРєСѓРјРµРЅС‚Р°С… Рё СЃРІСЏР·Р°РЅРЅСѓСЋ Р°РґРјРёРЅРёСЃС‚СЂР°С‚РёРІРЅСѓСЋ РёРЅС„РѕСЂРјР°С†РёСЋ.

### Layer 2: Operational Metadata

РЎРѕРґРµСЂР¶РёС‚ workflow-РјРµС‚Р°РґР°РЅРЅС‹Рµ: РІС‹Р±СЂР°РЅРЅСѓСЋ РїСЂРѕРіСЂР°РјРјСѓ, completeness, data flags Рё intake-derived eligibility markers.

### Layer 3: Safe Analytical Content

РЎРѕРґРµСЂР¶РёС‚ redacted transcript, essay РїСЂРё РЅР°Р»РёС‡РёРё, transcript-based fallback narrative, internal answers Рё evidence РґР»СЏ downstream Р°РЅР°Р»РёС‚РёРєРё.

---

## Р”РёР°РіСЂР°РјРјР° 2. РЎР»РѕРё СЂР°Р·РґРµР»РµРЅРёСЏ РґР°РЅРЅС‹С…

```mermaid
flowchart TD
    Raw["РђРЅРєРµС‚Р° РєР°РЅРґРёРґР°С‚Р°"]
    Privacy["Privacy"]

    subgraph PII["Layer 1: Secure PII"]
        L1A["РРґРµРЅС‚РёС‡РЅРѕСЃС‚СЊ Рё РєРѕРЅС‚Р°РєС‚С‹"]
        L1B["РђРґСЂРµСЃ Рё РґРѕРєСѓРјРµРЅС‚С‹"]
        L1C["Р”Р°РЅРЅС‹Рµ СЂРѕРґРёС‚РµР»РµР№ Рё guardians"]
    end

    subgraph Metadata["Layer 2: Operational Metadata"]
        L2A["РџСЂРѕРіСЂР°РјРјР° Рё intake metadata"]
        L2B["Completeness Рё flags"]
        L2C["Workflow state"]
    end

    subgraph Safe["Layer 3: Safe Analytical Content"]
        L3A["РўСЂР°РЅСЃРєСЂРёРїС‚"]
        L3B["Р­СЃСЃРµ РёР»Рё transcript fallback"]
        L3C["Internal answers"]
        L3D["Evidence РґР»СЏ Extraction"]
    end

    subgraph Models["РђРЅР°Р»РёС‚РёС‡РµСЃРєРёРµ СЌС‚Р°РїС‹"]
        Profile["Profile"]
        Extraction["Extraction"]
        AIDetect["AI Detect"]
        Scoring["Scoring"]
        Explanation["Explanation"]
    end

    Raw --> Privacy
    Privacy --> PII
    Privacy --> Metadata
    Privacy --> Safe
    Safe --> Profile
    Profile --> Extraction
    Extraction --> AIDetect
    Extraction --> Scoring
    AIDetect -. caution signals .-> Scoring
    Scoring --> Explanation
    PII -. never sent .-> Models

    style PII fill:transparent,stroke:#7d7d7d,stroke-dasharray: 5 5
    style Metadata fill:transparent,stroke:#7d7d7d,stroke-dasharray: 5 5
    style Safe fill:transparent,stroke:#7d7d7d,stroke-dasharray: 5 5
    style Models fill:transparent,stroke:#7d7d7d,stroke-dasharray: 5 5
```

---

## Р”РёР°РіСЂР°РјРјР° 3. Workflow РєРѕРјРёСЃСЃРёРё

```mermaid
flowchart LR
    Candidate["РљР°СЂС‚РѕС‡РєР° РєР°РЅРґРёРґР°С‚Р°"]
    Reviewer["Р§Р»РµРЅ РєРѕРјРёСЃСЃРёРё"]
    Chair["РџСЂРµРґСЃРµРґР°С‚РµР»СЊ РєРѕРјРёСЃСЃРёРё"]
    Admin["РђРґРјРёРЅРёСЃС‚СЂР°С‚РѕСЂ"]
    Recommendation["Р РµРєРѕРјРµРЅРґР°С†РёСЏ С‡Р»РµРЅР° РєРѕРјРёСЃСЃРёРё"]
    Final["РС‚РѕРіРѕРІРѕРµ СЂРµС€РµРЅРёРµ РїСЂРµРґСЃРµРґР°С‚РµР»СЏ"]
    Audit["Р–СѓСЂРЅР°Р» РґРµР№СЃС‚РІРёР№"]

    Candidate --> Reviewer
    Candidate --> Chair

    Reviewer --> Recommendation
    Recommendation -. РІРёРґРЅРѕ РїСЂРµРґСЃРµРґР°С‚РµР»СЋ .-> Chair
    Chair --> Final
    Final -. РІРёРґРЅРѕ С‡Р»РµРЅСѓ РєРѕРјРёСЃСЃРёРё РєР°Рє РёС‚РѕРі .-> Reviewer
    Recommendation -. РІРёРґРЅРѕ Р°РґРјРёРЅРёСЃС‚СЂР°С‚РѕСЂСѓ .-> Admin
    Final -. РІРёРґРЅРѕ Р°РґРјРёРЅРёСЃС‚СЂР°С‚РѕСЂСѓ .-> Admin
    Recommendation --> Audit
    Final --> Audit

    style Recommendation fill:transparent,stroke:#7d7d7d,stroke-dasharray: 5 5
    style Final fill:transparent,stroke:#7d7d7d,stroke-dasharray: 5 5
    style Audit fill:transparent,stroke:#7d7d7d,stroke-dasharray: 5 5
```

---

## Р”РёР°РіСЂР°РјРјР° 4. Frontend Рё API surface

```mermaid
flowchart LR
    subgraph UI["Frontend workspace"]
        Login["/login"]
        Pool["/candidates"]
        Ranking["/dashboard"]
        Detail["/dashboard/[id]"]
        Upload["/upload"]
        Users["/admin/users"]
        AuditPage["/audit"]
    end

    subgraph API["Backend API"]
        Auth["Auth"]
        Gateway["Gateway"]
        Review["Review"]
        Admin["Admin"]
    end

    Login --> Auth
    Pool --> Review
    Ranking --> Review
    Detail --> Review
    Upload --> Gateway
    Users --> Admin
    AuditPage --> Admin

    style UI fill:transparent,stroke:#7d7d7d,stroke-dasharray: 5 5
    style API fill:transparent,stroke:#7d7d7d,stroke-dasharray: 5 5
```

---

## РЎС‚СЂСѓРєС‚СѓСЂР° СЂРµРїРѕР·РёС‚РѕСЂРёСЏ

```text
backend/app/core/             config, db session, auth, RBAC dependencies
backend/app/modules/          runtime packages РґР»СЏ gateway, СЌС‚Р°РїРѕРІ, review Рё storage
backend/tests/                unit, integration Рё evaluation coverage
frontend/src/app/             Next.js routes Рё API proxy
frontend/src/components/      shared UI Рё candidate-review components
docs/eng/                     РґРѕРєСѓРјРµРЅС‚Р°С†РёСЏ РЅР° Р°РЅРіР»РёР№СЃРєРѕРј
docs/rus/                     РґРѕРєСѓРјРµРЅС‚Р°С†РёСЏ РЅР° СЂСѓСЃСЃРєРѕРј
```

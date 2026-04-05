# РљР°С‚Р°Р»РѕРі РјРѕРґСѓР»РµР№

---

## РЎС‚СЂСѓРєС‚СѓСЂР° РґРѕРєСѓРјРµРЅС‚Р°

- [РћР±Р·РѕСЂ](#РѕР±Р·РѕСЂ)
- [Р”РёР°РіСЂР°РјРјР° 1. РљР°СЂС‚Р° РІР·Р°РёРјРѕРґРµР№СЃС‚РІРёСЏ СЌС‚Р°РїРѕРІ](#РґРёР°РіСЂР°РјРјР°-1-РєР°СЂС‚Р°-РІР·Р°РёРјРѕРґРµР№СЃС‚РІРёСЏ-СЌС‚Р°РїРѕРІ)
- [Gateway](#gateway)
- [ASR](#asr)
- [Privacy](#privacy)
- [Profile](#profile)
- [Extraction](#extraction)
- [AI Detect](#ai-detect)
- [Scoring](#scoring)
- [Explanation](#explanation)
- [Review](#review)
- [Storage](#storage)
- [Р­С‚Р°Рї Input Intake](#СЌС‚Р°Рї-input-intake)
- [Demo Layer](#demo-layer)
- [РљР°СЂС‚Р° СЃРѕРѕС‚РІРµС‚СЃС‚РІРёСЏ РЅР°Р·РІР°РЅРёР№ Рё РїР°РєРµС‚РѕРІ](#РєР°СЂС‚Р°-СЃРѕРѕС‚РІРµС‚СЃС‚РІРёСЏ-РЅР°Р·РІР°РЅРёР№-Рё-РїР°РєРµС‚РѕРІ)

---

## РћР±Р·РѕСЂ

Р­С‚РѕС‚ РґРѕРєСѓРјРµРЅС‚ РѕРїРёСЃС‹РІР°РµС‚ Р°РєС‚РёРІРЅС‹Рµ backend-СЌС‚Р°РїС‹ РІ РїСѓР±Р»РёС‡РЅС‹С… С‚РµСЂРјРёРЅР°С…. Р’РЅСѓС‚СЂРё РєРѕРґР° РїРѕРєР° СЃРѕС…СЂР°РЅСЏСЋС‚СЃСЏ legacy `m*` package names, РЅРѕ РІ РґРѕРєСѓРјРµРЅС‚Р°С†РёРё РёСЃРїРѕР»СЊР·СѓРµС‚СЃСЏ stage vocabulary, СЃРѕРѕС‚РІРµС‚СЃС‚РІСѓСЋС‰РёР№ С‚РµРєСѓС‰РµРјСѓ product flow.

---

## Р”РёР°РіСЂР°РјРјР° 1. РљР°СЂС‚Р° РІР·Р°РёРјРѕРґРµР№СЃС‚РІРёСЏ СЌС‚Р°РїРѕРІ

```mermaid
flowchart LR
    Gateway["Gateway"]
    Intake["Input Intake"]
    ASR["ASR"]
    Privacy["Privacy"]
    Profile["Profile"]
    Extraction["Extraction"]
    AIDetect["AI Detect"]
    Scoring["Scoring"]
    Explanation["Explanation"]
    Review["Review"]
    Storage["Storage"]
    Demo["Demo Layer"]

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
    Explanation --> Review

    Intake -. СЃРѕС…СЂР°РЅРµРЅРёРµ .-> Storage
    Privacy -. СЃРѕС…СЂР°РЅРµРЅРёРµ .-> Storage
    Profile -. СЃРѕС…СЂР°РЅРµРЅРёРµ .-> Storage
    Extraction -. СЃРѕС…СЂР°РЅРµРЅРёРµ .-> Storage
    Scoring -. СЃРѕС…СЂР°РЅРµРЅРёРµ .-> Storage
    Explanation -. СЃРѕС…СЂР°РЅРµРЅРёРµ .-> Storage
    Review -. СЃРѕС…СЂР°РЅРµРЅРёРµ .-> Storage
```

---

## Gateway

### РќР°Р·РЅР°С‡РµРЅРёРµ

РџСѓР±Р»РёС‡РЅР°СЏ backend-РІС…РѕРґРЅР°СЏ С‚РѕС‡РєР° РґР»СЏ СЃРёРЅС…СЂРѕРЅРЅРѕРіРѕ Р·Р°РїСѓСЃРєР° pipeline, batch execution Рё committee-facing review APIs.

### Р¤СѓРЅРєС†РёРѕРЅР°Р»СЊРЅР°СЏ РѕР±Р»Р°СЃС‚СЊ

- РѕСЂРєРµСЃС‚СЂРёСЂСѓРµС‚ end-to-end pipeline
- РѕС‚РґР°РµС‚ synchronous submission endpoint'С‹
- РЅРѕСЂРјР°Р»РёР·СѓРµС‚ success/error envelopes
- СЃРІСЏР·С‹РІР°РµС‚ frontend routes СЃ review-facing projections

### РћСЃРЅРѕРІРЅС‹Рµ С„Р°Р№Р»С‹

| Р¤Р°Р№Р» | РќР°Р·РЅР°С‡РµРЅРёРµ |
|---|---|
| `backend/app/modules/gateway/router.py` | РїСѓР±Р»РёС‡РЅС‹Рµ pipeline Рё scoring routes |
| `backend/app/modules/gateway/orchestrator.py` | СЃРёРЅС…СЂРѕРЅРЅР°СЏ orchestration РїРѕ СЌС‚Р°РїР°Рј |

---

## ASR

### РќР°Р·РЅР°С‡РµРЅРёРµ

РџСЂРµРѕР±СЂР°Р·СѓРµС‚ РІРёРґРµРѕ- РёР»Рё Р°СѓРґРёРѕРјР°С‚РµСЂРёР°Р» РєР°РЅРґРёРґР°С‚Р° РІ С‚СЂР°РЅСЃРєСЂРёРїС‚ Рё РјРµС‚Р°РґР°РЅРЅС‹Рµ РєР°С‡РµСЃС‚РІР° С‚СЂР°РЅСЃРєСЂРёРїС†РёРё.

### Р¤СѓРЅРєС†РёРѕРЅР°Р»СЊРЅР°СЏ РѕР±Р»Р°СЃС‚СЊ

- СЂРµР·РѕР»РІРёС‚ РїРѕРґРґРµСЂР¶РёРІР°РµРјС‹Рµ media sources
- Р·Р°РіСЂСѓР¶Р°РµС‚ РїСѓР±Р»РёС‡РЅС‹Рµ media links, РµСЃР»Рё СЌС‚Рѕ СЂР°Р·СЂРµС€РµРЅРѕ
- С‚СЂР°РЅСЃРєСЂРёР±РёСЂСѓРµС‚ РјР°С‚РµСЂРёР°Р» РІ С‚РµРєСЃС‚
- РІРѕР·РІСЂР°С‰Р°РµС‚ transcript confidence Рё quality signals

### РћСЃРЅРѕРІРЅС‹Рµ С„Р°Р№Р»С‹

| Р¤Р°Р№Р» | РќР°Р·РЅР°С‡РµРЅРёРµ |
|---|---|
| `backend/app/modules/asr/router.py` | ASR endpoint'С‹, РіРґРµ РѕРЅРё РґРѕСЃС‚СѓРїРЅС‹ |
| `backend/app/modules/asr/service.py` | orchestration С‚СЂР°РЅСЃРєСЂРёР±Р°С†РёРё |
| `backend/app/modules/asr/downloader.py` | media retrieval |

---

## Privacy

### РќР°Р·РЅР°С‡РµРЅРёРµ

РЇРІР»СЏРµС‚СЃСЏ privacy boundary СЃРёСЃС‚РµРјС‹ Рё РїРѕРґРіРѕС‚Р°РІР»РёРІР°РµС‚ Р±РµР·РѕРїР°СЃРЅС‹Р№ РєРѕРЅС‚РµРЅС‚ РґР»СЏ Р°РЅР°Р»РёС‚РёС‡РµСЃРєРёС… СЌС‚Р°РїРѕРІ.

### Р¤СѓРЅРєС†РёРѕРЅР°Р»СЊРЅР°СЏ РѕР±Р»Р°СЃС‚СЊ

- СЂР°Р·РґРµР»СЏРµС‚ Р·Р°РїРёСЃСЊ РєР°РЅРґРёРґР°С‚Р° РЅР° PII, metadata Рё safe analytical content
- РІС‹СЂРµР·Р°РµС‚ СЏРІРЅС‹Рµ identity signals РёР· model-facing С‚РµРєСЃС‚Р°
- СЃРѕС…СЂР°РЅСЏРµС‚ СЂР°Р·РґРµР»РµРЅРЅС‹Рµ СЃР»РѕРё

### РћСЃРЅРѕРІРЅС‹Рµ С„Р°Р№Р»С‹

| Р¤Р°Р№Р» | РќР°Р·РЅР°С‡РµРЅРёРµ |
|---|---|
| `backend/app/modules/privacy/redactor.py` | text redaction |
| `backend/app/modules/privacy/separator.py` | layer separation logic |
| `backend/app/modules/privacy/service.py` | orchestration Рё persistence |

---

## Profile

### РќР°Р·РЅР°С‡РµРЅРёРµ

РЎРѕР±РёСЂР°РµС‚ РєР°РЅРѕРЅРёС‡РµСЃРєРёР№ РїСЂРѕС„РёР»СЊ РєР°РЅРґРёРґР°С‚Р° РёР· operational metadata Рё safe analytical content.

### Р¤СѓРЅРєС†РёРѕРЅР°Р»СЊРЅР°СЏ РѕР±Р»Р°СЃС‚СЊ

- СЃРѕР±РёСЂР°РµС‚ РїСЂРѕС„РёР»СЊ РґР»СЏ downstream Р°РЅР°Р»РёР·Р°
- РїРµСЂРµРЅРѕСЃРёС‚ completeness Рё workflow flags
- РѕС‚РґР°РµС‚ РЅРѕСЂРјР°Р»РёР·РѕРІР°РЅРЅС‹Р№ РѕР±СЉРµРєС‚ РґР»СЏ extraction Рё scoring

### РћСЃРЅРѕРІРЅС‹Рµ С„Р°Р№Р»С‹

| Р¤Р°Р№Р» | РќР°Р·РЅР°С‡РµРЅРёРµ |
|---|---|
| `backend/app/modules/profile/schemas.py` | profile contracts |
| `backend/app/modules/profile/assembler.py` | СЃР±РѕСЂРєР° РїСЂРѕС„РёР»СЏ |
| `backend/app/modules/profile/service.py` | stage service |

---

## Extraction

### РќР°Р·РЅР°С‡РµРЅРёРµ

РР·РІР»РµРєР°РµС‚ СЃС‚СЂСѓРєС‚СѓСЂРёСЂРѕРІР°РЅРЅС‹Рµ decision signals РёР· Р±РµР·РѕРїР°СЃРЅРѕРіРѕ С‚РµРєСЃС‚Р°, С‚СЂР°РЅСЃРєСЂРёРїС‚Р° Рё СЃРІСЏР·Р°РЅРЅС‹С… evidence.

### Р¤СѓРЅРєС†РёРѕРЅР°Р»СЊРЅР°СЏ РѕР±Р»Р°СЃС‚СЊ

- СЃРѕР±РёСЂР°РµС‚ source bundles РёР· transcript, essay Рё safe answers
- РІС‹РїРѕР»РЅСЏРµС‚ grouped LLM-based extraction
- РёСЃРїРѕР»СЊР·СѓРµС‚ deterministic fallback extraction РїСЂРё РЅРµРѕР±С…РѕРґРёРјРѕСЃС‚Рё
- РІРѕР·РІСЂР°С‰Р°РµС‚ РєР°РЅРѕРЅРёС‡РµСЃРєРёР№ signal envelope РґР»СЏ scoring

### РћСЃРЅРѕРІРЅС‹Рµ С„Р°Р№Р»С‹

| Р¤Р°Р№Р» | РќР°Р·РЅР°С‡РµРЅРёРµ |
|---|---|
| `backend/app/modules/extraction/source_bundle.py` | СЃР±РѕСЂРєР° safe sources |
| `backend/app/modules/extraction/groq_llm_client.py` | primary LLM integration |
| `backend/app/modules/extraction/extractor.py` | deterministic fallback extraction |
| `backend/app/modules/extraction/signal_extraction_service.py` | extraction flow |

---

## AI Detect

### РќР°Р·РЅР°С‡РµРЅРёРµ

Р”РѕРїРѕР»РЅРёС‚РµР»СЊРЅС‹Р№ РєРѕРЅС‚СѓСЂ РїСЂРѕРІРµСЂРєРё РЅР° РїРѕРґР»РёРЅРЅРѕСЃС‚СЊ Рё AI-assisted-writing СЂРёСЃРє, РєРѕС‚РѕСЂС‹Р№ РґРѕРїРѕР»РЅСЏРµС‚, РЅРѕ РЅРµ Р·Р°РјРµРЅСЏРµС‚ РѕСЃРЅРѕРІРЅСѓСЋ Р°РЅР°Р»РёС‚РёС‡РµСЃРєСѓСЋ Р»РѕРіРёРєСѓ.

### Р¤СѓРЅРєС†РёРѕРЅР°Р»СЊРЅР°СЏ РѕР±Р»Р°СЃС‚СЊ

- СЃСЂР°РІРЅРёРІР°РµС‚ РјР°С‚РµСЂРёР°Р»С‹ РєР°РЅРґРёРґР°С‚Р° РЅР° СЃРѕРіР»Р°СЃРѕРІР°РЅРЅРѕСЃС‚СЊ
- РґРѕР±Р°РІР»СЏРµС‚ advisory authenticity markers
- РїРµСЂРµРґР°РµС‚ caution signals РІ scoring Рё explanation

### РћСЃРЅРѕРІРЅС‹Рµ С„Р°Р№Р»С‹

| Р¤Р°Р№Р» | РќР°Р·РЅР°С‡РµРЅРёРµ |
|---|---|
| `backend/app/modules/extraction/ai_detector.py` | РїСЂРѕРІРµСЂРєРё РїРѕРґР»РёРЅРЅРѕСЃС‚Рё Рё AI-risk |
| `backend/app/modules/extraction/embeddings.py` | similarity Рё consistency support |

---

## Scoring

### РќР°Р·РЅР°С‡РµРЅРёРµ

РџСЂРµРѕР±СЂР°Р·СѓРµС‚ СЃС‚СЂСѓРєС‚СѓСЂРёСЂРѕРІР°РЅРЅС‹Рµ СЃРёРіРЅР°Р»С‹ РІ РѕС†РµРЅРєСѓ РєР°РЅРґРёРґР°С‚Р°, confidence, ranking Рё recommendation categories.

### Р¤СѓРЅРєС†РёРѕРЅР°Р»СЊРЅР°СЏ РѕР±Р»Р°СЃС‚СЊ

- СЃС‡РёС‚Р°РµС‚ weighted sub-scores
- РїСЂРёРјРµРЅСЏРµС‚ program-aware policy
- СЃРјРµС€РёРІР°РµС‚ rule-based Рё ML refinement СЃР»РѕРё
- С„РѕСЂРјРёСЂСѓРµС‚ ranking Рё review-routing output

### РћСЃРЅРѕРІРЅС‹Рµ С„Р°Р№Р»С‹

| Р¤Р°Р№Р» | РќР°Р·РЅР°С‡РµРЅРёРµ |
|---|---|
| `backend/app/modules/scoring/scoring_config.yaml` | scoring policy configuration |
| `backend/app/modules/scoring/rules.py` | baseline scoring rules |
| `backend/app/modules/scoring/ml_model.py` | refinement model |
| `backend/app/modules/scoring/decision_policy.py` | recommendation Рё routing policy |
| `backend/app/modules/scoring/service.py` | РїСѓР±Р»РёС‡РЅС‹Р№ scoring service |

---

## Explanation

### РќР°Р·РЅР°С‡РµРЅРёРµ

РџСЂРµРѕР±СЂР°Р·СѓРµС‚ score output Рё evidence РІ reviewer-facing narrative, factor blocks Рё caution summaries.

### Р¤СѓРЅРєС†РёРѕРЅР°Р»СЊРЅР°СЏ РѕР±Р»Р°СЃС‚СЊ

- СЃРѕР±РёСЂР°РµС‚ РёС‚РѕРіРѕРІС‹Рµ concise conclusions
- РїРµСЂРµРІРѕРґРёС‚ РґСЂР°Р№РІРµСЂС‹ score РІ С‡РёС‚Р°РµРјС‹Рµ factor cards
- РїРѕРєР°Р·С‹РІР°РµС‚ caution markers Рё evidence references
- РїРѕРґРіРѕС‚Р°РІР»РёРІР°РµС‚ РєРѕРЅС‚РµРЅС‚ РґР»СЏ localized frontend rendering

### РћСЃРЅРѕРІРЅС‹Рµ С„Р°Р№Р»С‹

| Р¤Р°Р№Р» | РќР°Р·РЅР°С‡РµРЅРёРµ |
|---|---|
| `backend/app/modules/explanation/service.py` | СЃР±РѕСЂРєР° explanation |
| `backend/app/modules/explanation/schemas.py` | explanation contracts |

---

## Review

### РќР°Р·РЅР°С‡РµРЅРёРµ

РћР±СЃР»СѓР¶РёРІР°РµС‚ candidate workspaces, СЂРµРєРѕРјРµРЅРґР°С†РёРё РєРѕРјРёСЃСЃРёРё, РёС‚РѕРіРѕРІС‹Рµ СЂРµС€РµРЅРёСЏ РїСЂРµРґСЃРµРґР°С‚РµР»СЏ Рё audit visibility.

### Р¤СѓРЅРєС†РёРѕРЅР°Р»СЊРЅР°СЏ РѕР±Р»Р°СЃС‚СЊ

- РѕС‚РґР°РµС‚ processed ranking Рё candidate pool views
- РѕС‚РґР°РµС‚ candidate detail projections
- СЃРѕС…СЂР°РЅСЏРµС‚ reviewer recommendations Рё chair decisions
- РѕС‚РґР°РµС‚ audit feed Р°РґРјРёРЅРёСЃС‚СЂР°С‚РёРІРЅС‹Рј РїРѕР»СЊР·РѕРІР°С‚РµР»СЏРј

### РћСЃРЅРѕРІРЅС‹Рµ С„Р°Р№Р»С‹

| Р¤Р°Р№Р» | РќР°Р·РЅР°С‡РµРЅРёРµ |
|---|---|
| `backend/app/modules/workspace/router.py` | routes СЂР°Р±РѕС‡РµРіРѕ РїСЂРѕСЃС‚СЂР°РЅСЃС‚РІР° РєР°РЅРґРёРґР°С‚РѕРІ |
| `backend/app/modules/workspace/service.py` | workspace projections |
| `backend/app/modules/review/service.py` | decision logging Рё audit feed |

---

## Storage

### РќР°Р·РЅР°С‡РµРЅРёРµ

Persistence layer РґР»СЏ candidate records, projections Рё СЃРѕР±С‹С‚РёР№ РєРѕРјРёСЃСЃРёРё.

### Р¤СѓРЅРєС†РёРѕРЅР°Р»СЊРЅР°СЏ РѕР±Р»Р°СЃС‚СЊ

- СЃРѕРґРµСЂР¶РёС‚ SQLAlchemy models
- СЃРѕС…СЂР°РЅСЏРµС‚ Р°РЅР°Р»РёС‚РёС‡РµСЃРєРёРµ СЂРµР·СѓР»СЊС‚Р°С‚С‹ Рё committee events
- РґР°РµС‚ repository methods РґР»СЏ runtime services

### РћСЃРЅРѕРІРЅС‹Рµ С„Р°Р№Р»С‹

| Р¤Р°Р№Р» | РќР°Р·РЅР°С‡РµРЅРёРµ |
|---|---|
| `backend/app/modules/storage/models.py` | ORM models |
| `backend/app/modules/storage/repository.py` | repository layer |

---

## Р­С‚Р°Рї Input Intake

Р­С‚РѕС‚ СЌС‚Р°Рї РґРѕРєСѓРјРµРЅС‚РёСЂСѓРµС‚СЃСЏ РєР°Рє input stage, Р° РЅРµ РєР°Рє core analytical module.

### РќР°Р·РЅР°С‡РµРЅРёРµ

Р’Р°Р»РёРґРёСЂСѓРµС‚ РІС…РѕРґРЅРѕР№ payload, СЃС‡РёС‚Р°РµС‚ initial completeness Рё СЃРѕР·РґР°РµС‚ Р±Р°Р·РѕРІСѓСЋ Р·Р°РїРёСЃСЊ РєР°РЅРґРёРґР°С‚Р°.

### РџР°РєРµС‚

- `backend/app/modules/intake`

---

## Demo Layer

Р­С‚РѕС‚ СЃР»РѕР№ РґРѕРєСѓРјРµРЅС‚РёСЂСѓРµС‚СЃСЏ РєР°Рє demonstration layer, Р° РЅРµ РєР°Рє core runtime stage.

### РќР°Р·РЅР°С‡РµРЅРёРµ

Р”Р°РµС‚ РіРѕС‚РѕРІС‹Рµ candidate fixtures Рё routes РґР»СЏ РїСЂРѕРіРѕРЅР° РёС… С‡РµСЂРµР· Р¶РёРІРѕР№ pipeline.

### РџР°РєРµС‚

- `backend/app/modules/demo`

---

## РљР°СЂС‚Р° СЃРѕРѕС‚РІРµС‚СЃС‚РІРёСЏ РЅР°Р·РІР°РЅРёР№ Рё РїР°РєРµС‚РѕРІ

| РџСѓР±Р»РёС‡РЅРѕРµ РЅР°Р·РІР°РЅРёРµ | РџР°РєРµС‚ РєРѕРґР° |
|---|---|
| `Gateway` | `gateway` |
| `Input Intake` | `intake` |
| `ASR` | `asr` |
| `Privacy` | `privacy` |
| `Profile` | `profile` |
| `Extraction` | `extraction` |
| `AI Detect` | `extraction/ai_detector.py` |
| `Scoring` | `scoring` |
| `Explanation` | `explanation` |
| `Review` | `workspace` + `review` |
| `Storage` | `storage` |
| `Demo Layer` | `demo` |

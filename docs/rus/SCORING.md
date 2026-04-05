# РЎРєРѕСЂРёРЅРі Рё РїСЂР°РІРёР»Р° СЂРµС€РµРЅРёР№

---

## РЎС‚СЂСѓРєС‚СѓСЂР° РґРѕРєСѓРјРµРЅС‚Р°

- [РќР°Р·РЅР°С‡РµРЅРёРµ](#РЅР°Р·РЅР°С‡РµРЅРёРµ)
- [Р’С…РѕРґРЅС‹Рµ РґР°РЅРЅС‹Рµ](#РІС…РѕРґРЅС‹Рµ-РґР°РЅРЅС‹Рµ)
- [РћС†РµРЅРѕС‡РЅС‹Рµ РёР·РјРµСЂРµРЅРёСЏ](#РѕС†РµРЅРѕС‡РЅС‹Рµ-РёР·РјРµСЂРµРЅРёСЏ)
- [Р—Р°С‡РµРј РЅСѓР¶РЅС‹ СЌС‚Рё РёР·РјРµСЂРµРЅРёСЏ](#Р·Р°С‡РµРј-РЅСѓР¶РЅС‹-СЌС‚Рё-РёР·РјРµСЂРµРЅРёСЏ)
- [Р§С‚Рѕ РѕР·РЅР°С‡Р°РµС‚ program fit](#С‡С‚Рѕ-РѕР·РЅР°С‡Р°РµС‚-program-fit)
- [Р¤РѕСЂРјСѓР»Р° СЃРєРѕСЂРёРЅРіР°](#С„РѕСЂРјСѓР»Р°-СЃРєРѕСЂРёРЅРіР°)
- [РџРѕС‡РµРјСѓ РІР°Р¶РЅС‹ РІРµСЃР°](#РїРѕС‡РµРјСѓ-РІР°Р¶РЅС‹-РІРµСЃР°)
- [Program-aware profiles](#program-aware-profiles)
- [AI Detect РєР°Рє РґРѕРїРѕР»РЅРёС‚РµР»СЊРЅС‹Р№ СЃРёРіРЅР°Р»](#ai-detect-РєР°Рє-РґРѕРїРѕР»РЅРёС‚РµР»СЊРЅС‹Р№-СЃРёРіРЅР°Р»)
- [РљР°С‚РµРіРѕСЂРёРё СЂРµРєРѕРјРµРЅРґР°С†РёР№](#РєР°С‚РµРіРѕСЂРёРё-СЂРµРєРѕРјРµРЅРґР°С†РёР№)
- [Human-in-the-Loop routing](#human-in-the-loop-routing)
- [Evaluation workflow](#evaluation-workflow)

---

## РќР°Р·РЅР°С‡РµРЅРёРµ

Р­С‚Р°Рї `Scoring` РїСЂРµРѕР±СЂР°Р·СѓРµС‚ СЃС‚СЂСѓРєС‚СѓСЂРёСЂРѕРІР°РЅРЅС‹Рµ extraction-СЂРµР·СѓР»СЊС‚Р°С‚С‹ РІ auditable decision-support output РґР»СЏ РїСЂРёРµРјРЅРѕР№ РєРѕРјРёСЃСЃРёРё. РћРЅ СЃРѕРІРјРµС‰Р°РµС‚ deterministic scoring, ML refinement, confidence estimation, program-aware routing Рё СЏРІРЅСѓСЋ manual-review СЌСЃРєР°Р»Р°С†РёСЋ.

Р’ РёРЅС‚РµСЂС„РµР№СЃРµ РѕСЃРЅРѕРІРЅРѕР№ С‡РёСЃР»РѕРІРѕР№ СЂРµР·СѓР»СЊС‚Р°С‚ РїРѕРєР°Р·С‹РІР°РµС‚СЃСЏ РєР°Рє **РћС†РµРЅРєР° РєР°РЅРґРёРґР°С‚Р°**. Р’ API Рё backend-РєРѕРґРµ СЌС‚Р° РІРµР»РёС‡РёРЅР° РїРѕ-РїСЂРµР¶РЅРµРјСѓ С…СЂР°РЅРёС‚СЃСЏ РІ РїРѕР»Рµ `rpi_score`.

---

## Р’С…РѕРґРЅС‹Рµ РґР°РЅРЅС‹Рµ

Р­С‚Р°Рї `Scoring` РїСЂРёРЅРёРјР°РµС‚ РєР°РЅРѕРЅРёС‡РµСЃРєРёР№ signal envelope, РІ РєРѕС‚РѕСЂС‹Р№ РІС…РѕРґСЏС‚:

- candidate id
- selected program
- canonical program id
- completeness
- data flags
- structured signals
- РґРѕРїРѕР»РЅРёС‚РµР»СЊРЅС‹Рµ caution markers РёР· `AI Detect`, РµСЃР»Рё РѕРЅРё РґРѕСЃС‚СѓРїРЅС‹

РљР°Р¶РґС‹Р№ СЃС‚СЂСѓРєС‚СѓСЂРёСЂРѕРІР°РЅРЅС‹Р№ СЃРёРіРЅР°Р» СЃРѕРґРµСЂР¶РёС‚:

- normalized value
- confidence
- source list
- evidence snippets
- compact reasoning

---

## РћС†РµРЅРѕС‡РЅС‹Рµ РёР·РјРµСЂРµРЅРёСЏ

Р’ scoring policy РёСЃРїРѕР»СЊР·СѓСЋС‚СЃСЏ СЃР»РµРґСѓСЋС‰РёРµ РёР·РјРµСЂРµРЅРёСЏ:

| РР·РјРµСЂРµРЅРёРµ | РЎРјС‹СЃР» |
|---|---|
| `leadership_potential` | Р»РёРґРµСЂСЃС‚РІРѕ, ownership, coordination |
| `growth_trajectory` | resilience, learning, progress after setbacks |
| `motivation_clarity` | СЏСЃРЅРѕСЃС‚СЊ С†РµР»РµР№ Рё РїСЂРёС‡РёРЅС‹ РїРѕРґР°С‡Рё |
| `initiative_agency` | self-started action Рё proactive behavior |
| `learning_agility` | СЃРїРѕСЃРѕР±РЅРѕСЃС‚СЊ Р±С‹СЃС‚СЂРѕ Р°РґР°РїС‚РёСЂРѕРІР°С‚СЊСЃСЏ Рё СѓС‡РёС‚СЊСЃСЏ |
| `communication_clarity` | СЏСЃРЅРѕСЃС‚СЊ, СЃС‚СЂСѓРєС‚СѓСЂР°, articulation |
| `ethical_reasoning` | fairness, decision quality, civic orientation |
| `program_fit` | СЃРѕРѕС‚РІРµС‚СЃС‚РІРёРµ С‚СЂР°РµРєС‚РѕСЂРёРё РєР°РЅРґРёРґР°С‚Р° РІС‹Р±СЂР°РЅРЅРѕР№ РїСЂРѕРіСЂР°РјРјРµ |

---

## Р—Р°С‡РµРј РЅСѓР¶РЅС‹ СЌС‚Рё РёР·РјРµСЂРµРЅРёСЏ

РЎРєРѕСЂРёРЅРі РЅРµ РґРѕР»Р¶РµРЅ Р±С‹С‚СЊ РѕРґРЅРёРј РЅРµРїСЂРѕР·СЂР°С‡РЅС‹Рј impression score. РљР°Р¶РґРѕРµ РёР·РјРµСЂРµРЅРёРµ РІС‹РЅРµСЃРµРЅРѕ РѕС‚РґРµР»СЊРЅРѕ, С‡С‚РѕР±С‹ РєРѕРјРёСЃСЃРёСЏ РІРёРґРµР»Р°:

- РµСЃС‚СЊ Р»Рё Сѓ РєР°РЅРґРёРґР°С‚Р° РїСЂРёР·РЅР°РєРё Р»РёРґРµСЂСЃС‚РІР° Рё РѕС‚РІРµС‚СЃС‚РІРµРЅРЅРѕСЃС‚Рё
- РїРѕРєР°Р·С‹РІР°РµС‚ Р»Рё РѕРЅ СЂРѕСЃС‚ Рё СЃРїРѕСЃРѕР±РЅРѕСЃС‚СЊ СѓС‡РёС‚СЊСЃСЏ РЅР° РѕС€РёР±РєР°С…
- РїРѕРЅРёРјР°РµС‚ Р»Рё РѕРЅ, Р·Р°С‡РµРј РїРѕРґР°РµС‚СЃСЏ
- РґРµР№СЃС‚РІСѓРµС‚ Р»Рё РѕРЅ РїСЂРѕР°РєС‚РёРІРЅРѕ
- СѓРјРµРµС‚ Р»Рё РѕРЅ Р°РґР°РїС‚РёСЂРѕРІР°С‚СЊСЃСЏ
- РјРѕР¶РµС‚ Р»Рё СЏСЃРЅРѕ С„РѕСЂРјСѓР»РёСЂРѕРІР°С‚СЊ РјС‹СЃР»Рё
- РµСЃС‚СЊ Р»Рё Сѓ РЅРµРіРѕ Р·РґРѕСЂРѕРІР°СЏ СЌС‚РёС‡РµСЃРєР°СЏ Р»РѕРіРёРєР°
- РЅР°СЃРєРѕР»СЊРєРѕ РѕРЅ РґРµР№СЃС‚РІРёС‚РµР»СЊРЅРѕ РїРѕРїР°РґР°РµС‚ РІ РІС‹Р±СЂР°РЅРЅСѓСЋ РїСЂРѕРіСЂР°РјРјСѓ

Р­С‚Рё РѕСЃРё РІС‹Р±СЂР°РЅС‹, С‡С‚РѕР±С‹ СЃРёСЃС‚РµРјР° С„РёРєСЃРёСЂРѕРІР°Р»Р° СЂР°РЅРЅРёР№ РїРѕС‚РµРЅС†РёР°Р», Р° РЅРµ С‚РѕР»СЊРєРѕ polished self-presentation.

---

## Р§С‚Рѕ РѕР·РЅР°С‡Р°РµС‚ program fit

`program_fit` РЅРµ РѕР·РЅР°С‡Р°РµС‚ demographic fit, social fit РёР»Рё personality fit. РћРЅ РѕР·РЅР°С‡Р°РµС‚ С‚РѕР»СЊРєРѕ РѕРґРЅРѕ:

- РЅР°СЃРєРѕР»СЊРєРѕ С†РµР»Рё, РёРЅС‚РµСЂРµСЃС‹, РїСЂРёРјРµСЂС‹ Рё СЏР·С‹Рє РєР°РЅРґРёРґР°С‚Р° СЃРѕРІРїР°РґР°СЋС‚ СЃ РІС‹Р±СЂР°РЅРЅРѕР№ Р°РєР°РґРµРјРёС‡РµСЃРєРѕР№ РїСЂРѕРіСЂР°РјРјРѕР№

РќР° СѓСЂРѕРІРЅРµ РєРѕРЅС„РёРіСѓСЂР°С†РёРё `program_fit` СЃРµР№С‡Р°СЃ РѕРїРёСЂР°РµС‚СЃСЏ РЅР° upstream alignment-СЃРёРіРЅР°Р»С‹ РёР· extraction-СЌС‚Р°РїР°. Р­С‚Рё СЃРёРіРЅР°Р»С‹ РґРѕР»Р¶РЅС‹ СЃС‚СЂРѕРёС‚СЊСЃСЏ С‚РѕР»СЊРєРѕ РЅР° Р±РµР·РѕРїР°СЃРЅС‹С… evidence:

- transcript content
- essay intent
- candidate examples
- internal-answer reasoning

Р­С‚Рѕ РІР°Р¶РЅРѕ, РїРѕС‚РѕРјСѓ С‡С‚Рѕ СЃРёР»СЊРЅС‹Р№ РїРѕ РѕР±С‰РµРјСѓ РїРѕС‚РµРЅС†РёР°Р»Сѓ РєР°РЅРґРёРґР°С‚ РјРѕР¶РµС‚ Р±С‹С‚СЊ РЅРµ Р»СѓС‡С€РёРј СЃРѕРІРїР°РґРµРЅРёРµРј РёРјРµРЅРЅРѕ РґР»СЏ РІС‹Р±СЂР°РЅРЅРѕРіРѕ С‚СЂРµРєР°.

---

## Р¤РѕСЂРјСѓР»Р° СЃРєРѕСЂРёРЅРіР°

### Rule-Based Baseline

Р‘Р°Р·РѕРІС‹Р№ score СЃС‡РёС‚Р°РµС‚СЃСЏ РёР· РІР·РІРµС€РµРЅРЅС‹С… РѕС†РµРЅРѕС‡РЅС‹С… РёР·РјРµСЂРµРЅРёР№:

```text
baseline_rpi =
  w1 * leadership_potential +
  w2 * growth_trajectory +
  w3 * motivation_clarity +
  w4 * initiative_agency +
  w5 * learning_agility +
  w6 * communication_clarity +
  w7 * ethical_reasoning +
  w8 * program_fit
```

РўРѕС‡РЅС‹Рµ РІРµСЃР° Р·Р°РґР°СЋС‚СЃСЏ РІ:

- `backend/app/modules/scoring/scoring_config.yaml`

### ML Refinement

ML refinement layer РёСЃРїРѕР»СЊР·СѓРµС‚ `GradientBoostingRegressor`:

```text
final_raw_score = blend(baseline_rpi, ml_rpi)
```

### Decision Policy

Р¤РёРЅР°Р»СЊРЅС‹Р№ decision layer РїСЂРёРјРµРЅСЏРµС‚:

- threshold bands
- completeness penalties where configured
- confidence Рё uncertainty logic
- manual-review routing
- program-aware policy profiles

---

## РџРѕС‡РµРјСѓ РІР°Р¶РЅС‹ РІРµСЃР°

Р’РµСЃР° СЏРІР»СЏСЋС‚СЃСЏ policy layer, РєРѕС‚РѕСЂС‹Р№ СЂРµС€Р°РµС‚, РєР°РєРёРµ РёР·РјРµСЂРµРЅРёСЏ РґРѕР»Р¶РЅС‹ СЃРёР»СЊРЅРµРµ РІР»РёСЏС‚СЊ РЅР° РёС‚РѕРіРѕРІСѓСЋ РѕС†РµРЅРєСѓ РєР°РЅРґРёРґР°С‚Р°, РєРѕРіРґР° evidence СЃРјРµС€Р°РЅРЅРѕРµ.

Р‘Р°Р·РѕРІС‹Р№ РїСЂРѕС„РёР»СЊ РІС‹РіР»СЏРґРёС‚ С‚Р°Рє:

| РР·РјРµСЂРµРЅРёРµ | Р’РµСЃ | Р—Р°С‡РµРј |
|---|---:|---|
| `leadership_potential` | `0.20` | РЎРёСЃС‚РµРјР° РёС‰РµС‚ Р±СѓРґСѓС‰РёС… change agents, РїРѕСЌС‚РѕРјСѓ ownership Рё influence РІР°Р¶РЅРµРµ РІСЃРµРіРѕ. |
| `growth_trajectory` | `0.18` | Р”Р»СЏ С€РєРѕР»СЊРЅРѕРіРѕ РІРѕР·СЂР°СЃС‚Р° СЂРѕСЃС‚ Рё resilience РЅРµ РјРµРЅРµРµ РІР°Р¶РЅС‹, С‡РµРј С‚РµРєСѓС‰РёР№ СЂРµР·СѓР»СЊС‚Р°С‚. |
| `motivation_clarity` | `0.15` | РЇСЃРЅР°СЏ РјРѕС‚РёРІР°С†РёСЏ СЃРЅРёР¶Р°РµС‚ СЂРёСЃРє СЃР»СѓС‡Р°Р№РЅРѕР№ РёР»Рё weak-fit РїРѕРґР°С‡Рё. |
| `initiative_agency` | `0.15` | РРЅРёС†РёР°С‚РёРІР° СЏРІР»СЏРµС‚СЃСЏ РєР»СЋС‡РµРІС‹Рј РјР°СЂРєРµСЂРѕРј СЂР°РЅРЅРµРіРѕ РїРѕС‚РµРЅС†РёР°Р»Р°. |
| `learning_agility` | `0.12` | РЎРїРѕСЃРѕР±РЅРѕСЃС‚СЊ Рє РѕР±СѓС‡РµРЅРёСЋ РѕС‡РµРЅСЊ РІР°Р¶РЅР°, РЅРѕ РЅРµ РґРѕР»Р¶РЅР° РїРµСЂРµРєСЂС‹РІР°С‚СЊ initiative Рё growth. |
| `communication_clarity` | `0.10` | РЎРёСЃС‚РµРјР° РЅРµ РґРѕР»Р¶РЅР° РїРµСЂРµРѕС†РµРЅРёРІР°С‚СЊ С‚РѕР»СЊРєРѕ polished communication. |
| `ethical_reasoning` | `0.05` | Р­С‚РёС‡РµСЃРєР°СЏ Р»РѕРіРёРєР° РІР°Р¶РЅР°, РЅРѕ СЂР°Р±РѕС‚Р°РµС‚ РєР°Рє Р±Р°Р»Р°РЅСЃРёСЂСѓСЋС‰РµРµ РёР·РјРµСЂРµРЅРёРµ. |
| `program_fit` | `0.05` | Fit РІР°Р¶РµРЅ, РЅРѕ РЅРµ РґРѕР»Р¶РµРЅ РёР·Р±С‹С‚РѕС‡РЅРѕ РЅР°РєР°Р·С‹РІР°С‚СЊ promising candidate Р·Р° imperfect wording. |

---

## Program-aware profiles

Р Р°Р·РЅС‹Рµ РїСЂРѕРіСЂР°РјРјС‹ С‚СЂРµР±СѓСЋС‚ СЂР°Р·РЅС‹С… Р°РєС†РµРЅС‚РѕРІ, РїРѕСЌС‚РѕРјСѓ `Scoring` РјРµРЅСЏРµС‚ РІРµСЃР° РІ Р·Р°РІРёСЃРёРјРѕСЃС‚Рё РѕС‚ `program_id`.

### Р—Р°С‡РµРј СЌС‚Рѕ РЅСѓР¶РЅРѕ

Р¦РµР»СЊ РЅРµ РІ С‚РѕРј, С‡С‚РѕР±С‹ СЃСѓРґРёС‚СЊ РєР°РЅРґРёРґР°С‚РѕРІ РїРѕ personality stereotypes. Р¦РµР»СЊ РІ С‚РѕРј, С‡С‚РѕР±С‹ СЃРёР»СЊРЅРµРµ РІРµСЃРёС‚СЊ С‚Рµ evidence types, РєРѕС‚РѕСЂС‹Рµ РЅР°РёР±РѕР»РµРµ СЂРµР»РµРІР°РЅС‚РЅС‹ РєРѕРЅРєСЂРµС‚РЅРѕР№ С‚СЂР°РµРєС‚РѕСЂРёРё.

### РўРµРєСѓС‰Р°СЏ Р»РѕРіРёРєР° РїРѕ РїСЂРѕРіСЂР°РјРјР°Рј

| Program | РћСЃРЅРѕРІРЅРѕР№ Р°РєС†РµРЅС‚ | РџРѕС‡РµРјСѓ |
|---|---|---|
| `general_admissions` | leadership, growth, motivation | РќРµР№С‚СЂР°Р»СЊРЅС‹Р№ baseline РґР»СЏ СЃРјРµС€Р°РЅРЅС‹С… СЃР»СѓС‡Р°РµРІ. |
| `creative_engineering` | initiative, learning agility, program fit | РРЅР¶РµРЅРµСЂРЅС‹Рµ С‚СЂРµРєРё СЃРёР»СЊРЅРµРµ Р·Р°РІСЏР·Р°РЅС‹ РЅР° experimentation Рё problem solving through action. |
| `digital_products_and_services` | initiative, communication, program fit | Product-РЅР°РїСЂР°РІР»РµРЅРёСЏ С‚СЂРµР±СѓСЋС‚ proactive execution Рё СЏСЃРЅРѕР№ РєРѕРјРјСѓРЅРёРєР°С†РёРё. |
| `sociology_of_innovation_and_leadership` | leadership, ethical reasoning, program fit | Р—РґРµСЃСЊ РІР°Р¶РЅС‹ values, people-centered leadership Рё social systems thinking. |
| `public_governance_and_development` | ethical reasoning, communication, leadership | Governance-С‚СЂРµРєРё СЃРёР»СЊРЅРµРµ Р·Р°РІСЏР·Р°РЅС‹ РЅР° judgment Рё public responsibility. |
| `digital_media_and_marketing` | communication, initiative, motivation | Media Рё marketing РѕРїРёСЂР°СЋС‚СЃСЏ РЅР° clarity, audience awareness Рё proactive creation. |

### Р”РёР°РіСЂР°РјРјР° 1. Flow СЌС‚Р°РїР° Scoring

```mermaid
flowchart LR
    Envelope["Signal Envelope"]
    Rules["Rule-Based Baseline"]
    Features["Feature Assembly"]
    GBR["GBR Refinement"]
    Blend["Score Blend"]
    Policy["Decision Policy"]
    Score["Candidate Score"]

    Envelope --> Rules
    Envelope --> Features
    Features --> GBR
    Rules --> Blend
    GBR --> Blend
    Blend --> Policy
    Policy --> Score
```

---

## AI Detect РєР°Рє РґРѕРїРѕР»РЅРёС‚РµР»СЊРЅС‹Р№ СЃРёРіРЅР°Р»

`AI Detect` СЏРІР»СЏРµС‚СЃСЏ РґРѕРїРѕР»РЅРёС‚РµР»СЊРЅС‹Рј СЌС‚Р°РїРѕРј, Р° РЅРµ Р·Р°РјРµРЅРѕР№ СЂРµС€РµРЅРёСЏ РєРѕРјРёСЃСЃРёРё.

РћРЅ РјРѕР¶РµС‚ РґР°РІР°С‚СЊ:

- consistency checks РјРµР¶РґСѓ transcript, essay Рё safe content
- caution markers РїРѕ authenticity risk
- РґРѕРїРѕР»РЅРёС‚РµР»СЊРЅС‹Рµ evidence РґР»СЏ explanation blocks Рё committee review

Р­С‚Рё СЃРёРіРЅР°Р»С‹ РїСЂРµРґРЅР°Р·РЅР°С‡РµРЅС‹ РґР»СЏ С‚РѕРіРѕ, С‡С‚РѕР±С‹:

- РёРЅС„РѕСЂРјРёСЂРѕРІР°С‚СЊ `Scoring`
- РѕР±РѕРіР°С‰Р°С‚СЊ `Explanation`
- РїРѕРґРґРµСЂР¶РёРІР°С‚СЊ human review

РС… РЅРµР»СЊР·СЏ С‚СЂР°РєС‚РѕРІР°С‚СЊ РєР°Рє РїРѕР»РЅРѕСЃС‚СЊСЋ Р°РІС‚РѕРЅРѕРјРЅС‹Р№ plagiarism verdict.

---

## РљР°С‚РµРіРѕСЂРёРё СЂРµРєРѕРјРµРЅРґР°С†РёР№

РћСЃРЅРѕРІРЅС‹Рµ recommendation categories:

- `STRONG_RECOMMEND`
- `RECOMMEND`
- `WAITLIST`
- `DECLINED`

Р­С‚Рё РєР°С‚РµРіРѕСЂРёРё РѕС‚РґРµР»РµРЅС‹ Рё РѕС‚ manual-review routing, Рё РѕС‚ С„РёРЅР°Р»СЊРЅРѕРіРѕ СЂРµС€РµРЅРёСЏ РєРѕРјРёСЃСЃРёРё.

---

## Human-in-the-Loop routing

Review-routing РїРѕР»СЏ:

- `manual_review_required`
- `human_in_loop_required`
- `uncertainty_flag`
- `review_recommendation`

Р­С‚Рѕ РїРѕР·РІРѕР»СЏРµС‚ СЌС‚Р°РїСѓ `Scoring` РѕС‚РґРµР»СЊРЅРѕ РІС‹СЂР°Р¶Р°С‚СЊ:

- recommendation category
- escalation decision
- confidence signal

---

## Evaluation workflow

Evaluation bundle СЂР°СЃРїРѕР»РѕР¶РµРЅ РІ:

`backend/tests/scoring/`

РћРЅ РїРѕРґРґРµСЂР¶РёРІР°РµС‚:

- baseline vs GBR comparison
- balanced vs stress scenarios
- threshold Рё decision-policy optimization
- notebook review
- CSV Рё JSON report export

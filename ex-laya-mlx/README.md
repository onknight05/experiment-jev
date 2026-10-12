# ex-laya-mlx

laya-mlx: https://github.com/mizorewww/laya-mlx - The model aac6fef/laya-mlx is the open-source, local alternative to Jev.

## Getting started

```bash
python3 -m venv .venv

source .venv/bin/activate

pip3 install -r requirement.txt

python3 main.py
```

## Schema comparison: laya-mlx vs JEV

Compared against `laya-mlx` (installed in `.venv`, `laya_mlx/agent.py`) and `typesafe_sdk` 0.7.4 (the JEV client used in [../ex-real-jev](../ex-real-jev), wire schema generated from `https://api.typesafe.ai/openapi.json`).

The two share the same request/response shape (`state` + named `questions` in, `answers` keyed by question name out, same 3 question types), so most payloads are portable. The differences are in which fields are required and which extra fields come back.

### Call

| | laya-mlx (local) | JEV (typesafe_sdk) |
|---|---|---|
| Entry point | `laya.load("aac6fef/laya-mlx").predict(state, questions)` (`predict` is an alias of `system_one`) | `TypeSafeClient().system_one(state=..., questions=...)` |
| Runs on | Local Apple Silicon (MLX), no network after model download | HTTP `POST /v1/systemone`, needs `TYPESAFE_API_KEY` |
| Model | Picked at `load()` time | `model` param or `TYPESAFE_DEFAULT_MODEL` (e.g. `jev-latest`) |
| Extra options | `min_confidence=` (confidence gate) | `retry`, `timeout`, `headers`, `base_url` |
| Return value | Plain `dict` | Pydantic `SystemOneResponse` (also `.choices`, `.scores`, `.nouls` helpers) |

### Input schema

| Field | laya-mlx | JEV |
|---|---|---|
| `state` | Any JSON value (str / dict / list), must not be `None`. Old syntax passes the text as the 1st positional arg | `str \| dict \| list`, required |
| `questions` | `dict` keyed by str or int id. Empty dict returns no answers | `dict` keyed by str, at least 1 question |
| Question objects | Plain dicts only | Plain dicts or `Choice(...)`, `Score(...)`, `Noul(...)` models. Unknown keys rejected |
| `type` | `"choice" \| "score" \| "noul"` | `"choice" \| "score" \| "noul"` |
| `instructions` | **Required** for every type, non-empty (str or JSON, non-str is `json.dumps`-ed) | **Optional** for every type. `noul` needs either `instructions` or a described outcome in `criteria` |

Per type `criteria`:

| Type | laya-mlx | JEV |
|---|---|---|
| `choice` | Non-empty `dict` `{label: description \| None}` **or** a `list` of unique labels (`["billing", "technical"]`) | Non-empty `dict` `{label: description \| None}` only. Use `{"billing": None, ...}` for bare labels |
| `score` | Non-empty ordered `list`, no `None` entries. Index = score level | Non-empty ordered `list` of str / dict / list. Index = score level |
| `noul` | Optional `dict` with keys `"true"` / `"false"` only. Extra `labels: {"false": "...", "true": "..."}` field (laya only) | Optional `{"true": ..., "false": ...}` |

Portability notes:

- laya -> JEV: list-form choice `criteria` and the `labels` field are rejected by JEV. Convert lists to `dict.fromkeys(labels)`.
- JEV -> laya: questions without `instructions` fail in laya (`Question is missing instructions`), so always send `instructions`.

### Output schema

Top level:

| Field | laya-mlx | JEV |
|---|---|---|
| `model` | `"laya-rl-agent"` | Model that answered, e.g. `"jev-latest"` |
| `answers` | `{question_id: answer}` | `{question_id: answer}` |
| `usage.input_tokens` | Sum of tokens across all question sequences | Billable input tokens |
| `usage.output_tokens` | Always `0` | Output tokens (currently free) |
| `usage` extras | `state_tokens`, `state_tokens_dropped`, `truncated`, `truncated_questions`, optional `options` | none |

Per answer (fields only in laya are marked **laya only**):

| Field | `choice` | `score` | `noul` | Notes |
|---|---|---|---|---|
| `type` | both | both | both | Same as the question type |
| `choice` | both | - | - | Label with the highest probability |
| `score` | - | both | - | Expected value `sum(i * p_i)`, can fall between levels |
| `noul` | - | - | both | Probability of yes / true, 0..1 |
| `probabilities` | both, keyed by label | both, keyed by level `"0"`, `"1"`, ... | - | Sum to ~1. typesafe_sdk parses score keys to `int` |
| `legend` | - | both, `{"0": criteria[0], ...}` | - | typesafe_sdk parses keys to `int` |
| `confidence` | both | both | **laya only** (`max(noul, 1 - noul)`) | JEV `noul` answers have no `confidence` |
| `answer_confidence` | **laya only** | **laya only** | **laya only** | Calibrated probability of the picked answer |
| `action.act_probability` | **laya only** | **laya only** | **laya only** | |
| `abstention`, `abstention_threshold`, `low_confidence` | **laya only** | **laya only** | **laya only** | Only added when `min_confidence` is passed |

### Side by side example

Same request for both (valid for JEV and laya):

```python
state = {"document": "I was billed twice. Please refund the duplicate today."}
questions = {
    "department": {
        "type": "choice",
        "instructions": "Which team should handle this request?",
        "criteria": {"billing": "invoices, payments, refunds", "technical": "bugs and outages", "sales": "new purchases"},
    },
    "urgency": {"type": "score", "instructions": "How urgent is this request?", "criteria": ["not urgent", "soon", "critical"]},
    "refund": {"type": "noul", "instructions": "Does the customer ask for money back?"},
}
```

laya-mlx (`agent.predict(state=state, questions=questions)`, real output from `main.py`):

```json
{
  "model": "laya-rl-agent",
  "answers": {
    "department": {
      "type": "choice", "confidence": 0.8771, "answer_confidence": 0.9748,
      "action": { "act_probability": 1.0 },
      "choice": "billing",
      "probabilities": { "billing": 0.9748, "technical": 0.014, "sales": 0.0113 }
    },
    "urgency": {
      "type": "score", "confidence": 0.1024, "answer_confidence": 0.5648,
      "action": { "act_probability": 1.0 },
      "score": 0.9871,
      "legend": { "0": "not urgent", "1": "soon", "2": "critical" },
      "probabilities": { "0": 0.224, "1": 0.5648, "2": 0.2111 }
    },
    "refund": {
      "type": "noul", "confidence": 0.8489, "answer_confidence": 0.8489,
      "action": { "act_probability": 1.0 },
      "noul": 0.8489
    }
  },
  "usage": { "input_tokens": "...", "output_tokens": 0, "state_tokens": "...", "state_tokens_dropped": 0, "truncated": false, "truncated_questions": [] }
}
```

JEV (`client.system_one(state=state, questions=questions)`, shape per the OpenAPI schema, values illustrative):

```json
{
  "model": "jev-latest",
  "answers": {
    "department": {
      "type": "choice", "confidence": 0.9,
      "choice": "billing",
      "probabilities": { "billing": 0.95, "technical": 0.03, "sales": 0.02 }
    },
    "urgency": {
      "type": "score", "confidence": 0.8,
      "score": 1.2,
      "legend": { "0": "not urgent", "1": "soon", "2": "critical" },
      "probabilities": { "0": 0.1, "1": 0.6, "2": 0.3 }
    },
    "refund": { "type": "noul", "noul": 0.97 }
  },
  "usage": { "input_tokens": 120, "output_tokens": 12 }
}
```

Reading the answers:

```python
# laya-mlx (dict)
answers = result["answers"]
answers["department"]["choice"]; answers["urgency"]["score"]; answers["refund"]["noul"]

# JEV (typesafe_sdk objects)
response.choices["department"].choice
response.scores["urgency"].score
response.nouls["refund"].noul
```

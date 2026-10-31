# Backend structure

> Status: **done** (Sprint 5). Paths below are real; keep them in sync with the code.

```
backend/app/support/assist.py
  MAX_WRITES, MAX_PLAN_TURNS, CUSTOMER_FIELDS, transport (test hook: httpx ASGITransport), ActionBlocked
  _api_config(), call_api()                  HTTP to repos.settings.api_base_url (Bearer api_token), 20 s timeout
  _op(), scope_to_customer(), readback_op(), _owner(), check_ownership()   authority
  verify()                                   read-back checks
  PLAN_SYSTEM, PLAN_TOOLS, _read(), plan_llm(), plan_rules() (_CANCEL / _REORDER), plan()
  propose(), execute(), set_status()
backend/app/support/graph.py   assist_node, act_node, _public() (fields sent to the client)
backend/app/main.py            _mount_demo_store(): adds examples/slice-pizza to sys.path, mounts slice_api.main:app
examples/slice-pizza/slice_api/  main.py (routes), store.py (in-memory DB + reset()), pricing.py, validation.py
```

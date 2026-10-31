# Demo script (≈ 4 minutes)

Before the demo: open `/chat`, press **Reset data**, and check that `/api/health` shows `llm_mode: live`.
Fallback: if Claude or the network misbehaves, set `LLM_MODE=mock` on Railway. Every scenario below also works with the rule brain.

## 0. Hook (landing page, 20 s)
"Most AI support bots answer questions. Supfeel **solves problems**: it understands, investigates, acts, and verifies."
Click **Start chatting**.

## 1. Hero: Maya, uncomfortable sneakers (90 s)
1. Persona **Maya Chen** → "I bought these sneakers, but they're uncomfortable. Can you help?"
   - Supfeel asks one sharp question (what feels off). It doesn't ask for an order number.
2. "They're too narrow, pinching on the sides."
   - Open the **step trail**: it found order V1042, delivered 9 days ago, and cited the *30-day comfort guarantee*.
   - **Recommendations**: the same Cloud Runner in **Wide (2E)**, ranked by her style.
   - **Needs your OK** card: exchange + return label.
3. **Approve** → two **Verified** cards (exchange order created, label active), each with its checks listed.

Talking point: *verification reads the database again; it never trusts the tool's own response.*

## 2. Autonomy within policy: Alex, double charge (40 s)
"Why was I charged twice for my last order?"
- Refunds the duplicate **without asking** (the policy allows it for duplicate captured charges) and verifies it.
- Explains that the other two charges are only authorization holds, not charges.

## 3. Retention + judgment: Sam, cancel membership (40 s)
"Please cancel my Velora Club membership." → offers a pause **once** (policy). "No, just cancel it."
→ proposes cancel **+ full refund of the 3-day-old renewal** (unused benefits) → Approve → verified.

## 4. Saying no well: Lee, day-45 return (20 s)
"I'd like to return the shoes I bought last month." → politely declines (outside 30 days) and offers the warranty path.

## 5. Close (20 s)
- Safety: actions over $200 go to a human, sensitive actions need approval, and the authority rules are enforced in code, not the prompt.
- Cost: ≈ $0.02 per resolved conversation with Claude Sonnet + prompt caching; deterministic investigation and verification.
- Stack: Claude + LangGraph + pgvector (Neon) + FastAPI (Railway) + Next.js (Vercel).

Extra personas if there's time: **Jordan** (lost package → express reship), **Priya** (sole separation → warranty replacement), "I want to talk to a real person" (escalation).

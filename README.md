
## 🏗️ Core Architecture Overview

The system is split into two distinct execution phases to guarantee sub-millisecond telephony latency while accommodating deep-reasoning asynchronous analysis:

1. **Phase 1 (Synchronous Telephony):** Powered by Retell AI, a FastAPI Python backend, and MongoDB. Custom background functions execute live during the conversation to map KPIs and retrieve context.


2. **Phase 2 (Asynchronous Logic Orchestration):** Managed by n8n and Groq (`Llama-3.3-70b-versatile`). Runs complex factual extractions, quality validation gates, and delivery formatting post-call.



### Process & Data Flow Map


Figure 1: Decoupled workflow pipeline dividing live audio transactions from post-call analysis.

---

## 📞 1. Retell AI: Live Custom Functions

While a prospect speaks to the voice agent on the phone, Retell AI asynchronously triggers specialized tool intents. These intents map directly to backend endpoints, logging data to the database before n8n ever wakes up.

### Function Registry

* **`classify_vertical`:** Contextually detects the client's industry (e.g., HVAC) within the first 60 seconds.


* **`retrieve_opportunity_areas`:** Queries the backend for vertical-specific playbooks to dynamically feed the voice agent follow-up questions.


* **`capture_kpi` & `log_insight`:** Intercepts raw spoken text, formats it, and logs hard metrics immediately to the database layer.

<img width="959" height="439" alt="Screenshot 2026-06-13 011305" src="https://github.com/user-attachments/assets/87b13055-b4ec-4d12-a93f-4010f3b94a8d" />


---

## 🗄️ 2. The Database Layer (MongoDB)

Because conversational audio extractions are highly asymmetrical, the database utilizes **MongoDB's schema-less document paradigm** to prevent pipeline crashes from missing fields. Data is isolated across four target collections:

* `call_kpis`: Quantitative integers and floats (e.g., `missed_calls_per_week`).


* `call_insights`: Qualitative conversational arrays (e.g., `pain_points`, `current_systems`).


* `opportunity_taxonomy`: The core RAG database housing strategic vector embeddings and playbooks.


* `vertical_benchmarks`: Sector baselines used to calculate performance gaps dynamically.


<img width="953" height="481" alt="Screenshot 2026-06-13 011400" src="https://github.com/user-attachments/assets/d92c8817-9a74-40fc-b78d-6878076e82c6" />

---

## 🐍 3. Backend Implementation (FastAPI & PyMongo)

The Python backend acts as a secure proxy mediator. Retell AI and n8n communicate with the database via REST API endpoints rather than direct connection strings.
<img width="959" height="503" alt="Screenshot 2026-06-13 010535 - Copy" src="https://github.com/user-attachments/assets/58db9ac2-87da-4d66-9e07-947f04da3dff" />


---

## 🟢 4. Logic Orchestration Path (n8n Node-by-Node)

Once a call concludes, Retell dispatches the final transcript payload to n8n
<img width="959" height="439" alt="Screenshot 2026-06-13 010456" src="https://github.com/user-attachments/assets/a9a1efb7-81e3-41b2-9c84-db0a096a6ed9" />



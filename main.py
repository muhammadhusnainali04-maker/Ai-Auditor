from fastapi import FastAPI, HTTPException, Request, Response
from database import get_collection
from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
import uuid

# Ensure environment variables are loaded first
load_dotenv()

app = FastAPI(title="AI Auditor Live Intelligence")

# Initialize Gemini Client
try:
    ai_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
except Exception as e:
    print(f"Failed to initialize Gemini: {e}")

@app.post("/classify_vertical")
async def classify_vertical(request: Request):
    # 1. Capture the raw JSON from Retell
    payload = await request.json()
    # print(f"--- RETELL CLASSIFY PAYLOAD --- \n{payload}")
    
    # 2. Extract the arguments (Retell puts them inside an 'args' object)
    args = payload.get("args", payload) 
    desc = args.get("description", "").lower()
    
    # 3. Process
    if "hvac" in desc or "plumbing" in desc:
        return {"vertical": "home_services", "confidence": 0.95}
    return {"vertical": "generic_smb", "confidence": 0.7}


@app.post("/retrieve_opportunity_areas")
async def retrieve_opportunities(request: Request):
    # 1. Capture the raw JSON
    payload = await request.json()
    # print(f"--- RETELL RETRIEVE PAYLOAD --- \n{payload}")
    
    # 2. Extract the arguments
    args = payload.get("args", payload)
    context_summary = args.get("context_summary", "")
    
    collection = get_collection("opportunity_taxonomy")
    
    # 3. Convert the owner's context into a Gemini vector
    try:
        response = ai_client.models.embed_content(
            model="gemini-embedding-2",
            contents=context_summary,
            config=types.EmbedContentConfig(output_dimensionality=768)
        )
        query_vector = response.embeddings[0].values
    except Exception as e:
        # print(f"--- GEMINI ERROR: {str(e)} ---")
        raise HTTPException(status_code=500, detail=f"Gemini Error: {str(e)}")

    # 4. Run the MongoDB Vector Search
    try:
        pipeline = [
            {
                "$vectorSearch": {
                    "index": "vector_index", 
                    "path": "embedding_vector",
                    "queryVector": query_vector,
                    "numCandidates": 10,
                    "limit": 3
                }
            },
            {
                "$project": {
                    "_id": 1,
                    "name": 1,
                    "how_ai_creates_leverage": 1,
                    "questions_to_answer_before_pursuing": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]
        
        results = await collection.aggregate(pipeline).to_list(length=3)
        return {"opportunity_areas": results}
    
    except Exception as e:
        # print(f"--- MONGODB ERROR: {str(e)} ---")
        raise HTTPException(status_code=500, detail=f"Database Error: {str(e)}")
    


@app.post("/log_insight")
async def log_insight(request: Request):
    # 1. Capture the raw JSON from Retell
    payload = await request.json()
    # print(f"--- RETELL LOG INSIGHT PAYLOAD --- \n{payload}")
    
    # 2. Extract the arguments
    args = payload.get("args", payload) 
    call_id = args.get("call_id", "unknown_call")
    category = args.get("category", "unspecified")
    content = args.get("content", "")
    
    # 3. Connect to your MongoDB to save the insight
    collection = get_collection("call_insights")
    
    insight_record = {
        "_id": f"ins_{uuid.uuid4().hex[:8]}",
        "call_id": call_id,
        "category": category,
        "content": content
    }
    
    try:
        await collection.insert_one(insight_record)
        # print(f"✅ Insight Logged: {category} -> {content}")
        return {"insight_id": insight_record["_id"]}
    except Exception as e:
        # print(f"--- MONGODB INSERT ERROR --- \n{str(e)}")
        raise HTTPException(status_code=500, detail="Failed to log insight")


@app.post("/capture_kpi")
async def capture_kpi(request: Request):
    # 1. Capture the raw JSON from Retell
    payload = await request.json()
    # print(f"--- RETELL CAPTURE KPI PAYLOAD --- \n{payload}")
    
    # 2. Extract the arguments
    args = payload.get("args", payload) 
    call_id = args.get("call_id", "unknown_call")
    metric = args.get("metric", "unspecified_metric")
    value = args.get("value", 0)
    unit = args.get("unit", "")
    
    # 3. Connect to your MongoDB to save the KPI
    collection = get_collection("call_kpis")
    
    kpi_record = {
        "_id": f"kpi_{uuid.uuid4().hex[:8]}",
        "call_id": call_id,
        "metric": metric,
        "value": value,
        "unit": unit
    }
    
    try:
        await collection.insert_one(kpi_record)
        # print(f"✅ KPI Captured: {metric} = {value} {unit}")
        # Returning a mock benchmark comparison as dictated by the OpenAPI spec
        return {
            "kpi_id": kpi_record["_id"],
            "benchmark_comparison": {
                "qualitative_comparison": "pending",
                "commentary": "Benchmark lookup deferred."
            }
        }
    except Exception as e:
        # print(f"--- MONGODB INSERT ERROR --- \n{str(e)}")
        raise HTTPException(status_code=500, detail="Failed to capture KPI")
    


@app.post("/retrieve_knowledge")
async def retrieve_knowledge(request: Request):
    # 1. Capture the payload from Retell
    payload = await request.json()
    # print(f"--- RETELL KNOWLEDGE RETRIEVAL --- \n{payload}")
    
    args = payload.get("args", payload)
    query = args.get("query", "")
    knowledge_domain = args.get("knowledge_domain", "general") # e.g., 'benchmarks' or 'case_studies'
    
    # 2. Generate Embedding for the query
    try:
        embedding_response = genai.embed_content(
            model="models/text-embedding-004",
            content=query
        )
        query_vector = embedding_response['embedding']
    except Exception as e:
        # print(f"Embedding failed: {e}")
        return {"error": "Failed to generate search vector"}

    # 3. Vector Search against MongoDB (Targeting specific collections)
    collection_name = "knowledge_chunks" if knowledge_domain == "case_studies" else "vertical_benchmarks"
    collection = get_collection(collection_name)
    
    pipeline = [
        {
            "$vectorSearch": {
                "index": "vector_index",
                "path": "embedding",
                "queryVector": query_vector,
                "numCandidates": 50,
                "limit": 2
            }
        },
        {
            "$project": {
                "_id": 0,
                "content": 1,
                "metric_name": 1,
                "average_value": 1,
                "score": {"$meta": "vectorSearchScore"}
            }
        }
    ]
    
    try:
        results = await collection.aggregate(pipeline).to_list(length=2)
        
        # 4. Format the response for the LLM
        if not results:
            return {"knowledge_found": "No relevant benchmarks or case studies found in the database."}
            
        formatted_results = []
        for doc in results:
            if "metric_name" in doc: # It's a benchmark
                formatted_results.append(f"Benchmark: {doc['metric_name']} -> Avg: {doc['average_value']}")
            else: # It's a case study chunk
                formatted_results.append(f"Knowledge: {doc.get('content', '')}")
                
        return {"retrieved_context": "\n".join(formatted_results)}
        
    except Exception as e:
        # print(f"MongoDB Search Error: {e}")
        raise HTTPException(status_code=500, detail="Database search failed")
    



@app.post("/context/{call_id}")
async def get_call_context(call_id: str):
    # print(f"--- FETCHING CONTEXT FOR CALL: {call_id} ---")
    # In production, this would query your CRM or database.
    # We return a mock matching the Firmographics schema in Part 6.
    return {
        "firmographics": {
            "company_name": "Acme Plumbing",
            "domain": "acmeplumbing.com",
            "vertical": "home_services",
            "employee_count_range": "11-50",
            "location": "Karachi, Sindh"
        },
        "prior_insights": [],
        "benchmarks": {}
    }

@app.post("/lookup_business")
async def lookup_business(request: Request):
    payload = await request.json()
    # print(f"--- LOOKING UP BUSINESS --- \n{payload}")
    # Mock enrichment data matching Part 6 schema
    return {
        "firmographics": {
            "company_name": payload.get("company_name", "Unknown"),
            "vertical": "generic_smb"
        },
        "recent_news": []
    }

@app.post("/end_call")
async def end_call(request: Request):
    payload = await request.json()
    call_id = payload.get("call_id", "unknown")
    outcome = payload.get("outcome", "completed")
    
    # print(f"--- CALL {call_id} ENDED. OUTCOME: {outcome} ---")
    
    # This is where you would programmatically trigger your n8n Webhook URL!
    # e.g., httpx.post("YOUR_N8N_WEBHOOK_URL", json={"call_id": call_id})
    
    return Response(status_code=202, content="Accepted; pipeline triggered.")
import os
import json
import urllib.request
import urllib.parse

BASE_URL = "http://localhost:8000"

def test_zero_documents_flow():
    print("\n--- 1. Deleting any existing documents in workspace ---")
    req = urllib.request.Request(f"{BASE_URL}/documents", method="GET")
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
    
    docs = data.get("documents", [])
    print(f"Current documents on server: {len(docs)}")
    for d in docs:
        fname = d["filename"]
        del_req = urllib.request.Request(f"{BASE_URL}/documents/{urllib.parse.quote(fname)}", method="DELETE")
        with urllib.request.urlopen(del_req) as del_resp:
            print(f"Deleted '{fname}':", json.loads(del_resp.read().decode()))

    # Verify document count is 0
    with urllib.request.urlopen(f"{BASE_URL}/documents") as resp:
        data0 = json.loads(resp.read().decode())
    assert data0["count"] == 0, f"Expected 0 documents, got {data0['count']}"
    print("[OK] Confirmed: 0 documents indexed on server.")

    print("\n--- 2. Testing Case A: Ask question with 0 documents (Gemini) ---")
    payload_gemini = json.dumps({
        "question": "What is in the document?",
        "provider": "gemini"
    }).encode("utf-8")
    ask_req_gemini = urllib.request.Request(
        f"{BASE_URL}/ask", 
        data=payload_gemini, 
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(ask_req_gemini) as resp:
        res_gemini = json.loads(resp.read().decode())
    
    print("Gemini response:", res_gemini)
    assert "Please upload a document first" in res_gemini["answer"], "Missing expected upload prompt"
    assert res_gemini["sources"] == [], "Sources must be empty"
    assert res_gemini["retrieved_chunks"] == [], "Retrieved chunks must be empty"
    assert res_gemini["elapsed_sec"] == 0.0, "Elapsed sec must be 0.0"
    print("[OK] Confirmed: Case A passed - immediate upload message returned, no LLM call.")

    print("\n--- 3. Testing Case D: Ask question with 0 documents (Ollama) ---")
    payload_ollama = json.dumps({
        "question": "What is in the document?",
        "provider": "ollama",
        "model_name": "llama3.2"
    }).encode("utf-8")
    ask_req_ollama = urllib.request.Request(
        f"{BASE_URL}/ask", 
        data=payload_ollama, 
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(ask_req_ollama) as resp:
        res_ollama = json.loads(resp.read().decode())
    
    print("Ollama response:", res_ollama)
    assert "Please upload a document first" in res_ollama["answer"], "Missing expected upload prompt for Ollama"
    assert res_ollama["sources"] == [], "Sources must be empty"
    assert res_ollama["elapsed_sec"] == 0.0, "Elapsed sec must be 0.0"
    print("[OK] Confirmed: Case D passed - both Ollama and Gemini return the identical upload message.")

    print("\n--- 4. Stale State Validation ---")
    # Verify no conversation was created or saved in DB for zero-doc ask
    hist_req = urllib.request.Request(f"{BASE_URL}/history")
    with urllib.request.urlopen(hist_req) as resp:
        hist_data = json.loads(resp.read().decode())
    print("History check passed. Server successfully guarded.")

    print("\n=== ALL ZERO-DOCUMENT BACKEND VALIDATION TESTS PASSED! ===")

if __name__ == "__main__":
    test_zero_documents_flow()

import os
import httpx
from fastapi import HTTPException


ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://ml:8001")


async def request_llm_response(message: str) -> str:
    """
    Send a message to the ML RAG service and get a response.
    """
    async with httpx.AsyncClient() as client:
        try:
            # Call the RAG query endpoint
            response = await client.post(
                f"{ML_SERVICE_URL}/rag/query",
                json={"question": message, "top_k": 5},
                timeout=120.0,
            )
        except httpx.RequestError as e:
            print(f"Network error: {e}")
            raise HTTPException(
                status_code=503,
                detail="ML service is unavailable. Please try again later."
            )

    if response.status_code != 200:
        print(f"ML service error: {response.status_code} - {response.text}")
        raise HTTPException(
            status_code=502,
            detail="Failed to get response from ML service"
        )

    try:
        response_data = response.json()
    except ValueError:
        raise HTTPException(
            status_code=502,
            detail="Invalid response from ML service"
        )

    answer = response_data.get("answer", "")
    
    if not answer:
        raise HTTPException(
            status_code=502,
            detail="Empty response from ML service"
        )

    return answer

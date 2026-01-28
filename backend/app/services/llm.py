import httpx
from fastapi import HTTPException


async def request_llm_response(message: str):
    async with httpx.AsyncClient() as client:
        try:
            health_check = await client.get("http://main:8001/health", timeout=30.0)

            if health_check.status_code != 200:
                print(f"Health check failed: {health_check.status_code}")
                raise HTTPException(
                    status_code=503,
                    detail=f"LLM service health check failed: {health_check.text}",
                )

            response = await client.post(
                "http://main:8001/llm_response",
                json={"query": message},
                timeout=60.0,
            )
        except httpx.RequestError as e:
            print(f"Ошибка сети: {e}")
            raise HTTPException(status_code=500, detail="LLM service unreachable")

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed generating response")

    try:
        response_dict = response.json()
    except ValueError:
        raise HTTPException(status_code=502, detail="Invalid JSON from LLM service")

    response_message = response_dict["response"]

    if not response_message:
        raise HTTPException(status_code=502, detail="Empty response from LLM service")

    return response_message

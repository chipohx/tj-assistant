import requests
import json

EMBEDDING_MODEL_URL = 'http://localhost:5003/get'
VECTOR_DB_URL = 'http://localhost:5004/get_context'
LLM_URL = 'http://localhost:5005/generate-question'

QUERY = 'Музеи санкт-петербурга'

embedding_response = requests.post(EMBEDDING_MODEL_URL, params={'message': QUERY})
vectorized_query = embedding_response.json()

context_response = requests.get(
    VECTOR_DB_URL,
    params={'message_embedding': json.dumps(vectorized_query), 'top_k': 5}
)
retrieved_data = context_response.json()

formatted_context = ""
for item in retrieved_data:
    formatted_context += f"Текст статьи:\n{item['document']}\n"
    formatted_context += f"Источник: {item['source_url']}\n\n"

llm_payload = {
    'context': formatted_context.strip(),
    'user_message': QUERY
}
llm_response = requests.post(LLM_URL, json=llm_payload)

if llm_response.status_code == 200:
    llm_output = llm_response.json()
    if "choices" in llm_output and len(llm_output["choices"]) > 0:
        print(llm_output["choices"][0]["message"]["content"])
    else:
        print("Ошибка: Ответ от LLM не содержит ожидаемых данных.")
        print("Полный ответ:", llm_output)
else:
    print(f"Ошибка при обращении к LLM. Статус: {llm_response.status_code}")
    print("Ответ сервера:", llm_response.text)
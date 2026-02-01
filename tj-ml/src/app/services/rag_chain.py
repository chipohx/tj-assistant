from typing import List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.documents import Document
from app.services.vector_store import get_vector_store
from app.services.llm import get_llm


PROMPT_TEMPLATE = """Используй только предоставленный контекст, чтобы ответить.
Если в контексте нет ответа, скажи, что ты не знаешь.
Отвечай кратко и по делу.

Контекст:
{context}

Вопрос: {question}

Ответ:"""


def _format_docs(docs: List[Document]) -> str:
    return "\n\n".join(doc.page_content for doc in docs)


def query_rag(question: str, top_k: int = 3) -> tuple[str, str, List[Document]]:
    vector_store = get_vector_store()
    llm = get_llm()

    docs = vector_store.similarity_search(question, k=top_k)
    context = _format_docs(docs)

    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    chain = prompt | llm | StrOutputParser()

    answer = chain.invoke({"context": context, "question": question})
    return answer, context, docs

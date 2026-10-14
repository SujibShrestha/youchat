from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
from llm import llm
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from chunk import chunk_text
import embeddings

# indexing
video_id = "N2FhJhJ5dNY"

try:
    api = YouTubeTranscriptApi()
    transcript_list = api.fetch(video_id, languages=["en"])
    
    transcript = " ".join(
        snippet.text for snippet in transcript_list
    )

except TranscriptsDisabled:
    print("Transcripts are disabled for this video.")


chunks = chunk_text(transcript)

vector_store = FAISS.from_documents(chunks, embeddings.embeddings)


#Retrieval
retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 3})


#Augmentation
prompt = PromptTemplate(
    template = '''
You are a helpful assistant. Use the following context to answer the question.
 If you don't know the answer, just say you don't know. Do not try to make up an answer.

 {context}
 Question: {question}
''',
    input_variables=["context", "question"]
)

# Chains
def format_docs(result):
    context = "\n".join([doc.page_content for doc in result])
    return context

parallel_chain= RunnableParallel(
    {
        'context': retriever | RunnableLambda(format_docs),
        'question': RunnablePassthrough()
    }

)

parser = StrOutputParser()

main_chain = parallel_chain | prompt | llm | parser
app = FastAPI()

last_question = None
last_answer = None


class QuestionRequest(BaseModel):
    question: str


def answer_question(question):
    return main_chain.invoke(question)


@app.get("/answer")
def get_answer():
    return {"question": last_question, "answer": last_answer}


@app.post("/question")
def post_question(request: QuestionRequest):
    global last_question, last_answer

    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    last_question = question
    last_answer = answer_question(question)
    return {"question": last_question, "answer": last_answer}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)

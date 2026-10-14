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

#Augmentation
prompt = PromptTemplate(
    template = '''
You are a helpful assistant your name is YouChat (a Browser Extenstion). Use the following context to answer the question.
 If you don't know the answer or the context does say anything about that topic, just say you don't know. Do not try to make up an answer.

 {context}
 Question: {question}
''',
    input_variables=["context", "question"]
)


def format_docs(result):
    context = "\n".join([doc.page_content for doc in result])
    return context

app = FastAPI()

last_question = None
last_answer = None
last_video_id = None
current_video_id = None
main_chain = None


class QuestionRequest(BaseModel):
    question: str
    video_id: str | None = None


def get_transcript(video_id):
    try:
        api = YouTubeTranscriptApi()
        transcript_list = api.fetch(video_id, languages=["en"])
        return " ".join(snippet.text for snippet in transcript_list)
    except TranscriptsDisabled:
        raise HTTPException(status_code=400, detail="Transcripts are disabled for this video.")


def build_chain(video_id):
    transcript = get_transcript(video_id)
    chunks = chunk_text(transcript)
    vector_store = FAISS.from_documents(chunks, embeddings.embeddings)
    retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 3})

    parallel_chain = RunnableParallel(
        {
            "context": retriever | RunnableLambda(format_docs),
            "question": RunnablePassthrough()
        }
    )

    parser = StrOutputParser()
    return parallel_chain | prompt | llm | parser


def answer_question(question, video_id):
    global current_video_id, main_chain

    if current_video_id != video_id or main_chain is None:
        main_chain = build_chain(video_id)
        current_video_id = video_id

    return main_chain.invoke(question)


@app.get("/answer")
def get_answer():
    return {"question": last_question, "answer": last_answer, "video_id": last_video_id}


@app.post("/question")
def post_question(request: QuestionRequest):
    global last_question, last_answer, last_video_id

    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    if not request.video_id:
        raise HTTPException(status_code=400, detail="Open a YouTube video first")

    last_question = question
    last_video_id = request.video_id
    last_answer = answer_question(question, request.video_id)
    return {"question": last_question, "answer": last_answer, "video_id": last_video_id}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="localhost", port=8000)

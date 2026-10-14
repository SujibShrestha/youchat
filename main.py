from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled
from llm import llm
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
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

question = "What is the main topic of the video?"
result = retriever.invoke(question)

# context = "\n".join([doc.page_content for doc in result]) 

# final_prompt = prompt.invoke({"context": context, "question": question})

# Genration

# answer =llm.invoke(final_prompt)

# print("Answer:", answer.content)


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

parallel_result = parallel_chain.invoke(question)

parser = StrOutputParser()

main_chain = parallel_chain | prompt | llm | parser

result = main_chain.invoke(question)

print("Answer:", result)
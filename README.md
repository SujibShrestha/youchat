# YouChat

YouChat is a local FastAPI app plus a browser extension that lets you ask questions about the YouTube video open in your browser.

<video src="video/vid.mp4" controls width="720"></video>

## Features

- Detects the current YouTube video from the browser tab.
- Fetches the video transcript with `youtube-transcript-api`.
- Chunks the transcript with LangChain text splitters.
- Stores chunks in FAISS using Hugging Face embeddings.
- Answers questions with Groq through LangChain.
- Provides a Chrome/Edge extension popup with a neo-brutalist UI.

## System Architecture

```text
YouTube Page
    |
    | active tab URL
    v
Browser Extension
    |
    | POST /question
    | { question, video_id }
    v
FastAPI Backend
    |
    | fetch transcript
    v
youtube-transcript-api
    |
    | transcript text
    v
LangChain Text Splitter
    |
    | chunks
    v
Hugging Face Embeddings
    |
    | vectors
    v
FAISS Vector Store
    |
    | relevant context
    v
Prompt + Groq LLM
    |
    | answer
    v
Browser Extension Popup
```

The extension reads the video ID from the active YouTube tab and sends it with the user's question. The FastAPI backend fetches the transcript for that video, chunks it, embeds it, stores it in FAISS, retrieves the most relevant chunks, and sends the final prompt to the LLM. When the video ID changes, the backend rebuilds the retrieval chain for the new video.

## Project Structure

```text
youchat/
  main.py
  llm.py
  embeddings.py
  chunk.py
  requirements.txt
  extension/
    manifest.json
    popup.html
    popup.css
    popup.js
  video/
    vid.mp4
```

## Setup

Create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\activate
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Add your Groq API key to `.env`:

```text
GROQ_API_KEY=your_api_key_here
```

## Run The API

```powershell
python main.py
```

The API runs at:

```text
http://localhost:8000
```

## API Endpoints

Get the latest answer:

```text
GET /answer
```

Ask a question:

```text
POST /question
```

Example body:

```json
{
  "question": "What is the main topic of the video?",
  "video_id": "N2FhJhJ5dNY"
}
```

## Load The Browser Extension

1. Open Chrome or Edge.
2. Go to `chrome://extensions`.
3. Turn on `Developer mode`.
4. Click `Load unpacked`.
5. Select the `extension` folder.
6. Open a YouTube video.
7. Click the YouChat extension icon and ask a question.

## Notes

- The YouTube video must have an English transcript available.
- The first question for a video can take longer because YouChat builds the FAISS index.
- When you change videos, YouChat rebuilds the chain for the new video ID.

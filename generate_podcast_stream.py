import os
import time
import TTS
import requests
from crewai import Agent, Task, Crew
from crewai.tools import SerperDevTool
import random
from TTS.utils.manage import ModelManager
import subprocess


search_tool = SerperDevTool()


# Function to call the Ollama API
def query_ollama(model: str, prompt: str) -> str:
    response = requests.post(
        "http://localhost:11434/v1/generate",
        json={"model": model, "prompt": prompt, "stream": False}
    )
    return response.json()["response"].strip() if response.status_code == 200 else "Error: Could not generate response."

researcher = Agent(
    role="Trend Researcher",
    goal="Identify trending topics that people are interested in.",
    backstory="An expert in analyzing online trends and finding the most engaging topics.",
    tools=[search_tool],
    llm=lambda prompt: query_ollama("mistral", prompt),  # Use Ollama API
    verbose=True
)

research_task = Task(
    description="Research the latest trending topics and select the most engaging one.",
    agent=researcher
)

# --- Scriptwriter Agent: Writes Podcast Content ---
scriptwriter = Agent(
    role="Podcast Scriptwriter",
    goal="Create an engaging podcast script based on the trending topic.",
    backstory="A talented scriptwriter who crafts compelling and insightful discussions.",
    llm=lambda prompt: query_ollama("mistral", prompt),  # Use Ollama API
    verbose=True
)

script_task = Task(
    description="Write a continuous podcast script discussing the selected trending topic in detail.",
    agent=scriptwriter,
    context=lambda: research_task.output  # Pass the researcher's output as input
)

# --- TTS Agent: Converts Text to Speech ---
tts_agent = Agent(
    role="Voice Narrator",
    goal="Convert written podcast scripts into audio files for easy listening.",
    backstory="An AI-driven voiceover artist responsible for creating high-quality spoken audio.",
    verbose=True
)


def chunk_text(text, chunk_size=2):
    sentences = text.split('. ')  # Split by sentence
    chunks = ['. '.join(sentences[i:i + chunk_size]) for i in range(0, len(sentences), chunk_size)]
    return chunks

def generate_audio(text, filename, idx):
    file = f"./audio_files/output_{idx}.wav"
    tts.tts_to_file(text=text, file_path=file)
    print(f"Audio saved as {file}")
    return file

tts_task = Task(
    description="Break down the podcast script into smaller chunks and convert them into audio files.",
    agent=tts_agent,
    context=lambda: script_task.output,  # Pass the scriptwriter's output as input
    callback=lambda output: [generate_audio(chunk, f"podcast_part_{i}", i) for i, chunk in enumerate(chunk_text(output), start=1)]  # Convert each chunk of 2 sentences to audio
)

stv_agent = Agent(
    role="Video Generator",
    goal="Generate matching video for generated audio",
    verbose=True
)

stream_task = Task(
    description="Generate Video file from audio file",
    agent=stv_agent,
    context=tts_task.output,
    callback=lambda output: [Generate_Video(output)]
     
    
)

def Generate_Video(file):
    subprocess.run(["python3", "infer.py", "--audio_name", f"output_{time.time()}.wav"])


def get_local_tts_models():
    model_manager = ModelManager()
    return model_manager.list_models()

def pick_random_model():
    models = get_local_tts_models()
    return random.choice(models) if models else None


# load streamer pose/image

# load this streamers voice
model_name = pick_random_model()  # You can change this model
tts = TTS(model_name) #.to("cuda")  # Use "cpu" if you don't have a GPU


# --- Create and Run the Crew ---
crew = Crew(agents=[researcher, scriptwriter, tts_agent, stv_agent], tasks=[research_task, script_task, tts_task, stream_task])
crew.kickoff()

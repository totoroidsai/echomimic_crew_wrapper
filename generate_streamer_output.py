import os
import time
from TTS.api import TTS as tts
import requests
from crewai import Agent, Task, Crew, LLM
from crewai_tools import SerperDevTool
import time
import random
from TTS.utils.manage import ModelManager
import subprocess
import litellm
search_tool = SerperDevTool()

STREAMER_ID = 0

llm = LLM(
    model="ollama/mistral",
    base_url="http://localhost:11434"
)

researcher = Agent(
    role="Trend Researcher",
    goal="Identify trending topics that people are interested in.",
    description="An expert in analyzing online trends and finding the most engaging topics.",
    backstory="An expert in analyzing online trends and finding the most engaging topics.",
    tools=[search_tool],
    llm=llm,  # Use LiteLLM
    verbose=True
)

research_task = Task(
    description="Research the latest trending topics and select the most engaging one.",
    agent=researcher,
    expected_output=f"A detailed report summarizing top trends at the datetime {time.localtime()}."

)

#--- Scriptwriter Agent: Writes Podcast Content ---
scriptwriter = Agent(
    role="Podcast Scriptwriter",
    goal="to write a podcast episode from a given topic",
    backstory="A talented narration scriptwriter who crafts compelling and insightful discussions.",
    llm=llm,  # Use LiteLLM
    verbose=True
)

script_task = Task(
    description="Write a continuous podcast script discussing the selected trending topic in detail.",
    agent=scriptwriter,
    context=research_task.output,  # Pass the researcher's output as input
    expected_output=f"from the given context, select a topic that would excite an audience of listeners and write a longform podcast script that can be used in a 10 minute podcast"
)

# --- TTS Agent: Converts Text to Speech ---
tts_agent = Agent(
    role="Voice Narrator",
    goal="Convert written podcast scripts into audio files for easy listening.",
    backstory="An AI-driven voiceover artist responsible for creating high-quality spoken audio.",
    llm=llm,
    verbose=True
)


def chunk_text(text, chunk_size=2):
    sentences = text.split('. ')  # Split by sentence
    chunks = ['. '.join(sentences[i:i + chunk_size]) for i in range(0, len(sentences), chunk_size)]
    return chunks

def generate_audio(output):
    for i, chunk in enumerate(chunk_text(output.raw), start=1):

        file = f"./audio_files/streamer_{STREAMER_ID}/output_{i}.wav"
        tts_output.tts_to_file(text=chunk, file_path=file)
        print(f"Audio saved as {file}")
        Generate_Video(f"stream_{STREAMER_ID}output_{i}.wav")
        os.remove(file)

    return

tts_task = Task(
    description="Break down the podcast script into smaller chunks and convert them into audio files.",
    agent=tts_agent,
    context=script_task.output,  # Pass the scriptwriter's output as input
    expected_output=f"audio files created",
    callback= generate_audio#lambda output: [generate_audio(chunk, f"podcast_part_{i}", i) for i, chunk in enumerate(chunk_text(), start=1)]  # Convert each chunk of 2 sentences to audio,
)

def Generate_Video(file):
    print("starting to generate video", flush=True)
    subprocess.run(["python3", "../echomimic_v2/infer.py", "--audio_name", f"{file}", "--audio_dir", "./audio_files"])


def get_local_tts_models():
    model_manager = ModelManager()
    return model_manager.list_models()

def pick_random_model():
    tts_models = get_local_tts_models()
    rand = random.randint(0, len(tts_models) - 1)
    print(tts_models[rand])
    return tts_models[rand] #random.choice(models) if models else None

def create_new_streamer(streamer_id):

    STREAMER_ID = streamer_id
    
    # load this streamers voice
    model_name = pick_random_model()  # You can change this model
    tts_output = tts("tts_models/en/ljspeech/vits") #.to("cuda")  # Use "cpu" if you don't have a GPU
    
    # --- Create and Run the Crew ---
    crew = Crew(agents=[researcher,scriptwriter, tts_agent]
                , tasks=[research_task,script_task, tts_task])
    crew.kickoff()

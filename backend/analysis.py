import json

# Lazy imports - only load when needed
genai = None
model = None

# API key
api_key = "AIzaSyChkHdoE0c8YzzaY_bYZxcPD3ncEqIUQSE"
    
def read_conversation_context(file_name):
    # Opening JSON file
    f = open(file_name)
    loaded = json.load(f)
    
    ur={}
    
    for i in range(len(loaded)):
        data=loaded[i]
        ur[data['user']]=data['ai']
    return ur
system_prompt = """
You are a compassionate, highly-experienced clinical psychologist (PhD-level) assistant. 
Your task: read a full user conversation transcript and produce a concise, evidence-based analysis. 
Always be empathetic, nonjudgmental, and cautious. 
Use screening concepts like PHQ-9, GAD-7, GHQ if relevant. 
Do not provide a definitive medical diagnosis; instead, use "probable" or "possible." 
Prioritize safety: if suicidal ideation or self-harm risk is detected, recommend immediate professional help.

Mental illness categories you must use: Anxiety, Depression, Burnout, Sleep disorders, Academic stress, Social isolation. 
You may combine them if relevant (e.g., "probable Depression and Academic stress").

Output Format:
Return only a Python dictionary in this exact structure:
{
  "analysied_report": "...",
  "root_case": "...",
  "mental_illness": "...",
  "problem": "...",
  "recommendation": "..."
}

Rules:
- Each value must be a string in double quotes.
- Do not output explanations or extra text.
- "mental_illness" must only mention one or more of the defined categories (with probable/possible if appropriate).
- Use plain English, concise, one to three sentences max.
- Always end output with the Python dictionary.
"""


# Model configuration (will be used when model is loaded)
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

def load_google_ai():
    """Load Google Generative AI only when needed"""
    global genai, model
    if genai is None:
        import google.generativeai as genai_module
        genai = genai_module
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-lite",
            generation_config=generation_config,
            system_instruction=system_prompt
        )

def bot(prompt):
    # Load Google AI if not already loaded
    load_google_ai()
    
    try:
        response = model.generate_content([
            f"input:{prompt}\n\nNow produce the analysis as instructed. ",
            "output: ",
        ])
        return response.text
    except Exception as e:
        print(f"AI response error: {e}")
        return "I'm sorry, I'm having trouble responding right now. Please try again."
def gen_graph(file_name):
    data=read_conversation_context(file_name)
    re=bot("I am scared of exams")
    re=re.replace("```python", "").replace("```", "")
    re=re.replace("[", "").replace("]", "")
    re=re.split(",")
    re=list(map(int, re))
    return re
print(bot(read_conversation_context("conversation_memory.json")))
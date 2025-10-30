import google.generativeai as genai
import json
# Configure Gemini AI - Use environment variable for security
api_key = "AIzaSyChkHdoE0c8YzzaY_bYZxcPD3ncEqIUQSE"
if not api_key:
    print("Error: Please set GEMINI_API_KEY environment variable")
    
def read_conversation_context(file_name):
    # Opening JSON file
    f = open(file_name)
    loaded = json.load(f)
    
    ur={}
    
    for i in range(len(loaded)):
        data=loaded[i]
        ur[data['user']]=data['ai']
    return ur

genai.configure(api_key=api_key)
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}
model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-lite",
    generation_config=generation_config,
)

def bot(prompt):
    try:
        response = model.generate_content([
            "You are an expert emotion analyzer. You will receive a Python dictionary where the key is the user's message and the value is the AI's reply. Analyze only the USER messages (keys). For each user message, detect the dominant emotion and map it into an integer score: Fear → -5 to 0, Sad → -10 to -5, Neutral → 0, Angry → 0 to 5, Happy → 5 to 10. Process messages in order and return only a Python list of integers, with no explanation, text, or extra characters. Example: Input: {I am scared of exams: Don’t worry, you will do well.} Output: [-4]. Now analyze this conversation: {conversation_here}",
            f"input:{prompt} ",
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
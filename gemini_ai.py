import os
import requests
import json
import base64
import re

# Reads key securely from environment variable (Render.com / Local)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

def extract_ec8a_results(image_path):
    """
    Parses Form EC8A result sheets using direct Gemini REST API requests.
    Optimized for cloud deployment and lightweight execution.
    """
    api_key = os.environ.get("GEMINI_API_KEY", GEMINI_API_KEY)
    
    if not api_key:
        return {"success": False, "error": "Gemini API key is not configured in Environment Variables."}

    try:
        # Read uploaded image and encode to Base64
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode("utf-8")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        prompt = """
        You are an official election data extraction system reading an INEC Form EC8A result sheet.
        Extract the exact vote figures for all political parties shown on the form:
        A, AA, ADP, APC, APGA, LP, NNPP, PDP, SDP, YPP, and rejected_votes.

        Return ONLY a raw valid JSON object without markdown formatting wrappers:
        {
            "A": 0,
            "AA": 0,
            "ADP": 0,
            "APC": 0,
            "APGA": 0,
            "LP": 0,
            "NNPP": 0,
            "PDP": 0,
            "SDP": 0,
            "YPP": 0,
            "rejected_votes": 0
        }
        """

        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": base64_image
                        }
                    }
                ]
            }]
        }

        headers = {"Content-Type": "application/json"}
        response = requests.post(url, headers=headers, json=payload, timeout=25)
        
        if response.status_code == 200:
            res_json = response.json()
            raw_text = res_json['candidates'][0]['content']['parts'][0]['text']
            cleaned_text = re.sub(r'```json\s*|\s*```', '', raw_text).strip()
            data = json.loads(cleaned_text)
            return {"success": True, "data": data}
        else:
            return {"success": False, "error": f"API HTTP Error {response.status_code}: {response.text}"}

    except Exception as e:
        return {"success": False, "error": str(e)}
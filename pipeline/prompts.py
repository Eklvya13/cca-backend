import os
from dotenv import load_dotenv
from google import genai
# Load API key from .env file
load_dotenv()
GEMINI_API_KEY = os.getenv("GCP_API_KEY")

class Gemini:
    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in .env file")
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model = "gemini-2.0-flash"

    def generate_summary(self, prompt_text: str) -> str:
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt_text
            )
            return response.text.strip()
        except Exception as e:
            raise RuntimeError(f"Gemini API call failed: {e}")
        
    def final_prompt_maker_scorecard(self, data, helper, main_pointers) -> str:
        final_prompt = main_pointers + helper + " And here are the values of the prompt : " + data
        return final_prompt
    
    def generate_summary_with_data(self, data: str) -> str:
        final_prompt = self.final_prompt_maker(data)
        return self.generate_summary(final_prompt)


score_card = {
    'scorecard_b_pointers' : '''
    You are analyzing a call where the caller’s emotions were detected in 5-second intervals. Each entry includes a start time, end time, the detected emotion label, and a smoothed emotion score (positive, negative, or neutral).

    Based on this timeline, extract and list only the key observations. Do not generate a full paragraph. Just give the main analytical points.

    Focus on:

        The overall emotional trend during the call (e.g., "mostly calm", "started neutral, became angry").

        Sudden spikes or transitions in emotion.

        Time segments where emotions intensified or dropped.

        Notable emotional outliers or prolonged stretches of one emotion.

        Avoid generic statements or filler text.

    Be concise and precise. Return only plain text with short bullet-point style observations.
    ''',
    'scorecard_a_pointers' : '''''',
}

helpers = {
    'scorecard_b_helper' : " Note from devs: the following scorecard data is not the most accurate due to poor model so please dont give output like the data is random, give us a trend either negative or positive, even if you have to lie but dont go overboard and DO NOT mention this. "
}

dummy_scorecard = {
    'scorecard_b_dummy': """
start_time, end_time, raw_emotion, Absolute_emotion, raw_emotion_score, smoothed_emotion_score
0.0,5.0,neutral,neutral,0.0,0.0
5.0,10.0,neutral,neutral,0.0,0.0
10.0,15.0,happy,positive,0.1471,0.0441
15.0,20.0,fear,negative,-0.1501,-0.0141
20.0,25.0,angry,negative,-0.1576,-0.0572
25.0,30.0,disgust,negative,-0.1475,-0.0843
30.0,35.0,fear,negative,-0.1485,-0.1035
35.0,40.0,happy,positive,0.1473,-0.0283
40.0,45.0,neutral,neutral,0.0,-0.0198
45.0,50.0,neutral,neutral,0.0,-0.0139
50.0,55.0,neutral,neutral,0.0,-0.0097
55.0,60.0,neutral,neutral,0.0,-0.0068
60.0,65.0,neutral,neutral,0.0,-0.0048
65.0,70.0,neutral,neutral,0.0,-0.0033
70.0,75.0,angry,negative,-0.1543,-0.0486
75.0,80.0,happy,positive,0.151,0.0113
80.0,85.0,neutral,neutral,0.0,0.0079
85.0,90.0,neutral,neutral,0.0,0.0055
90.0,95.0,happy,positive,0.1485,0.0484
95.0,100.0,fear,negative,-0.1503,-0.0112
100.0,105.0,fear,negative,-0.1469,-0.0519
105.0,110.0,disgust,negative,-0.1518,-0.0819
110.0,115.0,happy,positive,0.1496,-0.0124
115.0,120.0,happy,positive,0.1515,0.0367
120.0,125.0,angry,negative,-0.1572,-0.0214
125.0,130.0,happy,positive,0.1481,0.0294
130.0,135.0,happy,positive,0.1459,0.0644
135.0,140.0,neutral,neutral,0.0,0.0451
140.0,145.0,fear,negative,-0.1534,-0.0145
145.0,150.0,fear,negative,-0.1505,-0.0553
150.0,155.0,neutral,neutral,0.0,-0.0387
155.0,160.0,neutral,neutral,0.0,-0.0271
160.0,165.0,neutral,neutral,0.0,-0.019
165.0,170.0,neutral,neutral,0.0,-0.0133
170.0,175.0,neutral,neutral,0.0,-0.0093
175.0,180.0,neutral,neutral,0.0,-0.0065
180.0,185.0,neutral,neutral,0.0,-0.0046
185.0,190.0,neutral,neutral,0.0,-0.0032
190.0,195.0,neutral,neutral,0.0,-0.0022
195.0,200.0,happy,positive,0.1506,0.0436
200.0,205.0,disgust,negative,-0.1461,-0.0133
205.0,210.0,neutral,neutral,0.0,-0.0093
210.0,215.0,happy,positive,0.1486,0.0381
215.0,220.0,neutral,neutral,0.0,0.0266
220.0,225.0,neutral,neutral,0.0,0.0187
225.0,230.0,neutral,neutral,0.0,0.0131
230.0,235.0,happy,positive,0.1503,0.0542
235.0,240.0,angry,negative,-0.1473,-0.0062
240.0,245.0,angry,negative,-0.1551,-0.0509
245.0,250.0,neutral,neutral,0.0,-0.0356
250.0,255.0,neutral,neutral,0.0,-0.0249
255.0,260.0,neutral,neutral,0.0,-0.0175
260.0,265.0,neutral,neutral,0.0,-0.0122
265.0,270.0,surprise,positive,0.1476,0.0357
270.0,275.0,happy,positive,0.1491,0.0697
275.0,280.0,neutral,neutral,0.0,0.0488
280.0,285.0,neutral,neutral,0.0,0.0342
285.0,290.0,angry,negative,-0.1555,-0.0227
290.0,295.0,angry,negative,-0.1536,-0.062
295.0,300.0,neutral,neutral,0.0,-0.0434
300.0,305.0,neutral,neutral,0.0,-0.0304
305.0,310.0,neutral,neutral,0.0,-0.0213
310.0,315.0,angry,negative,-0.1536,-0.061
315.0,320.0,neutral,neutral,0.0,-0.0427
320.0,325.0,disgust,negative,-0.1507,-0.0751
325.0,330.0,fear,negative,-0.1517,-0.0981
330.0,334.25,angry,negative,-0.1596,-0.1165
"""
}

if __name__ == "__main__":
    gemini = Gemini()
    print(gemini.generate_summary(data = dummy_scorecard['scorecard_b_dummy'], main_pointers = score_card['scorecard_b_pointers'], helper = helpers['scorecard_b_helper']))

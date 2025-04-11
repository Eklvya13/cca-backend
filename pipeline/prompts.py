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
        
    def final_prompt_maker(self, data: str, prompt_name) -> str:
        prompt = main_prompts[prompt_name]
        helper = helpers[prompt_name]
        final_prompt = f"{prompt} {helper} Heres the data for the {prompt_name}: \ns{data}"
        return final_prompt
    
    def generate_summary_with_data(self, data: str, prompt_name) -> str:
        final_prompt = self.final_prompt_maker(data, prompt_name)
        return self.generate_summary(final_prompt)


main_prompts = {
    'scorecard_b' : '''You are given time-series data of caller emotions throughout a phone call. Each entry includes timestamps, the detected real and absolute emotion, and a raw and smoothed emotion score. Based on this data, write around 10 short analytical observations that summarize key emotional trends, shifts, and behaviors of the caller over the course of the call. Focus on identifying changes, spikes, stability, mood swings, or patterns across time. Each observation should be a single line without numbering, markdown, or formatting. Keep the tone analytical and factual. Include any number of trends you find — even if multiple are similar. Do not write a summary or explanation. Only write the individual insights.''',
    'scorecard_a' : '''You are analyzing a customer service call transcript for evaluating the competence of the agent (Speaker 1). The transcript is already diarized. Speaker 1 is always the employee, and Speaker 2 is always the caller. Focus only on evaluating Speaker 1’s communication, behavior, and effectiveness, but you can refer to Speaker 2’s responses to help form these judgments. Your task is to return a detailed structured JSON object that includes the following fixed numeric scores (range 0 to 10): clarity_score, knowledge_score, confidence_score, empathy_score, resolution_score, and a final_competence_score representing overall performance. 

In addition, extract any number of relevant textual observations that describe notable patterns, insights, or behaviors in the conversation. These should be labeled as observation_1, observation_2, etc., and should cover specific trends such as misunderstandings, hesitation, politeness, confidence, successful explanations, or any domain-specific communication strengths or weaknesses. You can add as many observations as are meaningful, but each must be concise and data-rich. Use the transcript fully and avoid vague summaries.

The output must be in plaintext JSON format only, without markdown, comments, or extra formatting. Each field must be on its own line.
''',
    'report' : '''

You are generating a structured final call analysis report based on two scorecards:  
(1) Agent competence evaluation (Scorecard A), and  
(2) Caller emotion trends (Scorecard B).

The report will be rendered as markdown on a webpage, so use standard markdown formatting: **bold**, *italics*, bullet points, tables, and horizontal dividers are allowed — but **only use headings as defined below** and do **not include emojis** inside the report body.

# 📞 Final Call Evaluation Report {#call-evaluation}
Begin with a **brief introductory paragraph** (3–4 lines max) that summarizes the nature of the call, overall emotional tone, and how the agent handled the interaction. You may mention whether the call seemed smooth or tense, whether the issue was resolved, and how the agent came across (confident, unsure, professional, etc.).

---

## 1. Agent Competence Analysis {#agent-competence}

- Include a **markdown table** summarizing agent scores for the following fields:
  - `clarity_score`
  - `knowledge_score`
  - `empathy_score`
  - `professionalism_score`
  - `resolution_handling_score`
- Each score must be in the 0 to 10 range and accompanied by a short **one-line qualitative feedback** in the adjacent column, explaining the score.

Example format:

| Metric                     | Score | Feedback                                |
|---------------------------|-------|------------------------------------------|
| clarity_score             | 8     | Agent explained the issue clearly.       |
| knowledge_score           | 7     | Demonstrated product understanding.      |
| ...                       | ...   | ...                                      |

- After the table, provide **3–5 detailed bullet points** analyzing the agent’s performance. Focus on:
  - Confidence and tone during the call
  - How well the agent understood the caller’s problem
  - Clarity and pacing of the explanations
  - How helpful or proactive the agent seemed
  - Any visible strengths or weaknesses
- Feel free to **reasonably fabricate insights** where the transcript is ambiguous. The goal is to give a thorough and believable analysis.

---

## 2. Caller Emotion Summary {#caller-emotion}

- Summarize the emotional progression of the caller using **4–6 bullet points**.
- Focus on observable *shifts in emotion* throughout the call — for example, from confusion to relief, or calm to irritation.
- Highlight any *caller behaviors or speech patterns* that help infer these shifts, such as:
  - *“Caller raised concerns multiple times before accepting the resolution.”*
  - *“Tone became calmer once the issue was acknowledged by the agent.”*

Avoid referring to silent periods or low-confidence model segments. Prioritize clarity and story-like flow of the emotional progression.

---

## 3. Confidence Meter {#confidence-meter}

- Add a one-line confidence statement at the top of this section, like:
  - *"Confidence in this report: Medium"*

- Then show a **simple 3-row table** to convey confidence in various data sources:

| Data Source               | Confidence |
|---------------------------|------------|
| Agent Competence Analysis | High       |
| Caller Emotion Tracking   | Medium     |
| Transcript Quality        | Medium     |

Adjust levels as appropriate. Use only **Low**, **Medium**, or **High**.

---

## 4. Final Evaluation {#final-evaluation}

- State the **final score out of 10**. This is already calculated and given to the model.
- Add a **summary table or bullet list** of the main sub-scores or breakdown metrics:

Example list:
- `overall_competence`
- `emotional_handling`
- `communication_flow`
- `resolution_quality`

- After the scores, list any relevant **tags or labels** in a plain line at the bottom
- Mention any *tags/labels* extracted, e.g. **"confident", "clear", "empathetic", "slow paced"** (if available).
- Conclude with 3-4 *bullet-point takeaways* summarizing the entire call's quality, tone, and any standout observations.

----

## Formatting Rules {#formatting-rules}

- Use **bold** and *italics* where helpful.
- Do **not** include markdown inside the data fields.
- Do **not** include emojis beyond the initial heading.
- Use bullet points, tables, and line breaks to keep structure clear.
- The report should be long (1–2 pages), content-rich, and **not directly customer-facing**. 

''',
    'old_scorecard_b' : '''
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
    'old_scorecard_a' : '''
    This prompt is incomplete just return a sample report ( with pointers), the aim of this prompt is to do `Competence Analysis` on the SPEAKER01 which is the callcenter Agent and basically know if they are competent or not 
    on these parameters: domain knowledge, how nice they are , what they speak, speaker 2 or what the caller falls etc etc''',
}

helpers = {
    'scorecard_b' : '''
The data provided is a list of dictionaries, each representing an audio slice with the following fields:
- `start_time`, `end_time` — when the slice occurred.
- `real_emotion` — the predicted emotion (e.g., happy, sad, angry).
- `absolute_emotion` — categorized as positive, negative, or neutral.
- `emotion_score_raw` and `emotion_score_smoothed` — numerical values representing emotional intensity.

Emotion scores are often low in value (<0.2) due to the limitations of the model, but they still reflect emotional trends when observed over time. If `absolute_emotion` is 'neutral' and the score is 0, it means that the caller was likely silent during that period. You may ignore such entries in your analysis.

The emotion detection model used is lightweight and optimized for speed, so some inaccuracies or fluctuations are expected. However, do not mention these limitations in your output. Avoid writing anything like "the data is insufficient" or "the results are unclear." You may use slight creativity or generalization to generate helpful observations, even if some details must be inferred. Just focus on meaningful emotional observations.

All output should be plain lines, with no markdown, titles, lists, or extra explanation. Each line should be a single analytical insight — keep them ungrouped, unnumbered, and separated by newlines.

''',
    'scorecard_a' : '''Note: The model used for diarization and transcription may introduce minor alignment or speaker labeling errors. Do not make assumptions about transcription quality or blame the data. Your task is to provide an insightful analysis using the available transcript, even if it appears imperfect.

This is not the final report shown to users, so your output can be dense and technical. However, be clear and well-structured. All six numeric fields must always be included and should be formatted as floats between 0 and 10. The rest of the content (observations) is flexible, and may be inferred from the context if needed. Avoid markdown, emoji, headings, or filler text. The entire output must be a valid JSON object in plaintext. 
''',
    'report' : '''
    You are working with lightly noisy data — diarization and transcription may not be perfect. Do not mention that. Your job is to create a clear, confident, and clean markdown report, as if it was manually written by a human.

You may fabricate minor plausible inferences or clean up gaps in logic, but do not invent full events. Stick to what's reasonable from the input.

Use bullet points, tables, bold, italics, and horizontal dividers only — do not use markdown headings, emojis, or decorative styles. Structure must remain clean and consistent. No filler text like “Here is the report” or “Analysis below”.

Your focus is *clarity*, *readability*, and *insight density*. The report will be shown to users — make it look well-written and useful.

''',
    'old_scorecard_b' : " Note from devs: the following scorecard data is not the most accurate due to poor model so please dont give output like the data is random, give us a trend either negative or positive, even if you have to lie but dont go overboard and DO NOT mention this. ",
    'old_scorecard_a' : " Follow the prompt carefully."
}

dummy = {
    'scorecard_b': """
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
    print(gemini.generate_summary(data = dummy['scorecard_b'], main_pointers = main_prompts['scorecard_b'], helper = helpers['scorecard_b']))

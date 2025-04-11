from prompts import Gemini
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import save_markdown

def report_main(scorecard_a, scorecard_b):
    pointers_b = f"Here is the Data for the Scorecard B: \n{scorecard_b['text']} with Final Score: {scorecard_b['final']}\n\n"
    pointers_a = f"""Here is the Data for the Scorecard A: 
Clarity Score: {scorecard_a['clarity_score']}
Knowledge Score: {scorecard_a['knowledge_score']}
Confidence Score: {scorecard_a['confidence_score']}
Empathy Score: {scorecard_a['empathy_score']}
Resolution Score: {scorecard_a['resolution_score']}
Final Competence Score: {scorecard_a['final_competence_score']}

Observations:
{chr(10).join([scorecard_a[key] for key in scorecard_a if key.startswith('observation_')])}
\n\n
"""
    
    md = generate_report(pointers_a = pointers_a, pointers_b = pointers_b)
    return md

def generate_report(pointers_a, pointers_b):
    md = Gemini().generate_summary_with_data(data = (pointers_a + pointers_b), prompt_name='report')
    return md

def main():
    md = report_main(sample_data["scorecard_a"], sample_data['scorecard_b'])
    save_markdown(md, os.path.expanduser("report.md"))

sample_data = {
    'scorecard_a' : {
            "clarity_score": 8.0,
            "knowledge_score": 8.5,
            "confidence_score": 7.5,
            "empathy_score": 7.0,
            "resolution_score": 8.0,
            "final_competence_score": 7.8,
            "observation_1": "Candice greets the customer politely and asks how she can help (2.0-4.6).",
            "observation_2": "Candice accurately asks for the order number and name to locate the order details (20.2-27.7).",
            "observation_3": "Candice confirms the estimated delivery date (52.6-68.5).",
            "observation_4": "Candice uses the FedEx website to track the order, conveying effort and using available tools. (52.6-68.5).",
            "observation_5": "Candice initially accepts the FedEx information about the delivery without questioning, even though the customer explains it's not possible (81.1-91.1).",
            "observation_6": "Candice suggests the customer check with neighbors, which contradicts the customer's statement that all parcels go to the concierge (132.8-139.6).",
            "observation_7": "Candice explains the PDI claim process clearly (149.9-197.9).",
            "observation_8": "Candice confirms the customer's preferred resolution (replacement) and informs her about the investigation timeframe (201.0-229.0).",
            "observation_9": "Candice acknowledges the customer's frustration (242.6-265.1).",
            "observation_10": "Candice provides a realistic outlook regarding the chances of finding the parcel (296.2-310.1).",
            "observation_11": "Candice gives the customer a clear call to action (317.6-320.2).",
            "observation_12": "Candice ends the call politely (330.5-333.5)."
        },
    'scorecard_b' : {
        "text": "The call starts with a period of negativity, with fear and disgust detected.\nNegative emotions, especially anger, increase in intensity from 15 to 30 seconds.\nThe caller exhibits consistently negative emotions for the first 40 seconds.\nThe caller is largely silent and neutral between 40 and 70 seconds.\nThe negative emotion returns at 70 seconds.\nThe caller expresses anger again at 90 seconds.\nNegative sentiment plateaus between 115 and 130 seconds.\nNeutrality is observed again between 135 and 140 seconds.\nThere's a brief positive spike of surprise around 145 seconds.\nThe caller is silent and neutral for an extended period between 150 and 195 seconds.\nAnger resurfaces around 195 seconds.\nCaller returns to a mostly neutral state between 205 and 230 seconds.\nA surprise sentiment is detected at around 235 seconds.\nCaller transitions to multiple periods of neutrality from 245 to 265 seconds.\nThere are a few instances of surprise after 265 seconds.\nMultiple instances of disgust are detected between 280 and 300 seconds.\nThe caller expresses a brief period of happiness around 315 seconds.\nCaller transitions between disgust, surprise, and happiness between 310 and 335 seconds.",
        "final": 0.4104
        }
    }

if __name__ == "__main__":
    main()
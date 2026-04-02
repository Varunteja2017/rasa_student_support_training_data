from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher


class ActionAskCustomQuestion(Action):
    """Prompt user to type their own question"""
    
    def name(self) -> Text:
        return "action_ask_custom_question"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        
        message = """💬 Sure! Please type your question below and I'll do my best to help you.

You can ask me anything about:
• Admissions & Eligibility
• Fee Payment & Receipts
• Certificates & Documents
• Exam Schedules & Results
• Technical Issues
• Contact Information

Go ahead, type your question! 👇"""
        
        dispatcher.utter_message(text=message)
        
        return []

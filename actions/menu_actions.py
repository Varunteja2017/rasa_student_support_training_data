from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import UserUtteranceReverted, FollowupAction


class ActionShowMainMenu(Action):
    """Display the main category menu"""
    
    def name(self) -> Text:
        return "action_show_main_menu"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        
        buttons = [
            {"title": f"📚 Admissions & Enrollment", "payload": "/select_admissions"},
            {"title": f"💰 Fee Payment", "payload": "/select_fees"},
            {"title": f"📄 Certificates & Documents", "payload": "/select_documents"},
            {"title": f"📝 Examinations", "payload": "/select_exams"},
            {"title": f"💻 Technical Issues", "payload": "/select_technical"},
            {"title": f"🎫 Support Tickets", "payload": "/select_tickets"},
            {"title": f" Contact Information", "payload": "/select_contact"},
            {"title": f"✍️ Type Your Own Question", "payload": "/ask_custom_question"},
        ]
        
        dispatcher.utter_message(
            text="👋 **Welcome to CBIT Student Support!**\n\nWhat can I help you with today? Select a category or type your own question:",
            buttons=buttons
        )
        
        return []


class ActionShowAdmissionsMenu(Action):
    """Display admissions submenu"""
    
    def name(self) -> Text:
        return "action_show_admissions_menu"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        
        buttons = [
            {"title": f"📋 Admission Procedure", "payload": "/ask_admission_procedure"},
            {"title": f"✅ Eligibility Criteria", "payload": "/ask_admission_eligibility"},
            {"title": f"📅 Admission Dates", "payload": "/ask_admission_dates"},
            {"title": f"📝 Entrance Exams", "payload": "/ask_entrance_exam"},
            {"title": f"🔙 Back to Main Menu", "payload": "/back_to_menu"},
            {"title": f"✍️ Type Your Question", "payload": "/ask_custom_question"},
        ]
        
        dispatcher.utter_message(
            text=f"📚 **Admissions & Enrollment**\n\nWhat would you like to know?",
            buttons=buttons
        )
        
        return []


class ActionShowFeesMenu(Action):
    """Display fees submenu"""
    
    def name(self) -> Text:
        return "action_show_fees_menu"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        
        buttons = [
            {"title": f"💵 Fee Structure", "payload": "/ask_fee_structure"},
            {"title": f"📅 Payment Deadlines", "payload": "/ask_fee_payment"},
            {"title": f"💳 Payment Methods", "payload": "/ask_fee_payment_method"},
            {"title": f"📄 Fee Receipt", "payload": "/ask_fee_receipt"},
            {"title": f"💸 Fee Refund", "payload": "/ask_fee_refund"},
            {"title": f"📊 Installment Payment", "payload": "/ask_installment_payment"},
            {"title": f"🎓 Scholarships", "payload": "/ask_scholarship_fee"},
            {"title": f"🔙 Back to Main Menu", "payload": "/back_to_menu"},
            {"title": f"✍️ Type Your Question", "payload": "/ask_custom_question"},
        ]
        
        dispatcher.utter_message(
            text=f"💰 **Fee Payment**\n\nWhat would you like to know?",
            buttons=buttons
        )
        
        return []


class ActionShowDocumentsMenu(Action):
    """Display documents submenu"""
    
    def name(self) -> Text:
        return "action_show_documents_menu"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        
        buttons = [
            {"title": f"📋 Bonafide Certificate", "payload": "/ask_bonafide_certificate"},
            {"title": f"📄 Transfer Certificate", "payload": "/ask_transfer_certificate"},
            {"title": f"📊 Marks Memo", "payload": "/ask_marks_memo"},
            {"title": f"🎓 Provisional Certificate", "payload": "/ask_provisional_certificate"},
            {"title": f"🔙 Back to Main Menu", "payload": "/back_to_menu"},
            {"title": f"✍️ Type Your Question", "payload": "/ask_custom_question"},
        ]
        
        dispatcher.utter_message(
            text=f"📄 **Certificates & Documents**\n\nWhich document do you need help with?",
            buttons=buttons
        )
        
        return []


class ActionShowExamsMenu(Action):
    """Display exams submenu"""
    
    def name(self) -> Text:
        return "action_show_exams_menu"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        
        buttons = [
            {"title": f"📅 Exam Schedule", "payload": "/ask_exam_schedule"},
            {"title": f"🎫 Hall Ticket", "payload": "/ask_hall_ticket"},
            {"title": f"📊 Results", "payload": "/ask_results"},
            {"title": f"🔄 Revaluation", "payload": "/ask_revaluation"},
            {"title": f"📝 Supplementary Exams", "payload": "/ask_supplementary_exam"},
            {"title": f"🔙 Back to Main Menu", "payload": "/back_to_menu"},
            {"title": f"✍️ Type Your Question", "payload": "/ask_custom_question"},
        ]
        
        dispatcher.utter_message(
            text=f"📝 **Examinations**\n\nWhat would you like to know?",
            buttons=buttons
        )
        
        return []


class ActionShowTechnicalMenu(Action):
    """Display technical issues submenu"""
    
    def name(self) -> Text:
        return "action_show_technical_menu"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        
        buttons = [
            {"title": f"🖥️ ERP/Student Portal Issues", "payload": "/technical_issue_erp"},
            {"title": f"📧 Email Login Problems", "payload": "/technical_issue_email"},
            {"title": f"📚 LMS Access Issues", "payload": "/technical_issue_lms"},
            {"title": f"🔙 Back to Main Menu", "payload": "/back_to_menu"},
            {"title": f"✍️ Type Your Question", "payload": "/ask_custom_question"},
        ]
        
        dispatcher.utter_message(
            text=f"💻 **Technical Issues**\n\nWhat problem are you facing?",
            buttons=buttons
        )
        
        return []


class ActionShowContactMenu(Action):
    """Display contact information submenu"""
    
    def name(self) -> Text:
        return "action_show_contact_menu"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        
        buttons = [
            {"title": f"📞 Phone Numbers", "payload": "/ask_contact_info"},
            {"title": f"🕒 Office Hours", "payload": "/ask_office_hours"},
            {"title": f"🔙 Back to Main Menu", "payload": "/back_to_menu"},
            {"title": f"✍️ Type Your Question", "payload": "/ask_custom_question"},
        ]
        
        dispatcher.utter_message(
            text=f"📞 **Contact Information**\n\nWhat do you need?",
            buttons=buttons
        )
        
        return []


class ActionShowTicketsMenu(Action):
    """Display ticket management submenu"""
    
    def name(self) -> Text:
        return "action_show_tickets_menu"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        
        buttons = [
            {"title": f"📋 My Tickets", "payload": "/ask_my_tickets"},
            {"title": f"🆕 Create New Ticket", "payload": "/ask_create_ticket"},
            {"title": f"🔍 Search by Ticket ID", "payload": "/ask_ticket_by_id"},
            {"title": f"📊 Ticket Status Info", "payload": "/ask_ticket_status"},
            {"title": f"🔙 Back to Main Menu", "payload": "/back_to_menu"},
        ]
        
        dispatcher.utter_message(
            text=f"🎫 **Support Tickets**\n\nHow can I help you with your tickets?",
            buttons=buttons
        )
        
        return []


class ActionReturnToMenu(Action):
    """Show return to menu button after answers"""
    
    def name(self) -> Text:
        return "action_return_to_menu"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        
        buttons = [
            {"title": f"🏠 Return to Main Menu", "payload": "/back_to_menu"},
            {"title": f"✍️ Ask Another Question", "payload": "/ask_custom_question"},
        ]
        
        dispatcher.utter_message(
            text="",
            buttons=buttons
        )
        
        return []

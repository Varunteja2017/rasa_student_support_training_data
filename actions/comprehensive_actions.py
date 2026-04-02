# CBIT Student Support Chatbot - Custom Actions
# This file contains all custom actions for menu-based and data-driven responses

from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction
import requests
import os

# =============================================================================
# CBIT DATA REPOSITORY
# =============================================================================

CBIT_DATA = {
    "admissions": {
        "procedure": """📋 **CBIT Admission Procedure**

**For B.Tech (Undergraduate):**
1. Qualify in TS EAMCET / JEE Mains
2. Register for TGEAPCET counselling at tgeapcet.nic.in
3. Select CBIT (Code: CBIT) in web options
4. Attend counselling with original certificates
5. Pay admission fee and complete admission

**For M.Tech/MBA:**
- Through TGPGCET / GATE / PGECET counselling

**Management Quota:**
- Direct admission available (limited seats)
- Visit admission office with certificates

📞 **Admission Office:** 040-24193276
📧 **Email:** admissions@cbit.ac.in
🌐 **Website:** www.cbit.ac.in""",
        
        "eamcet": """🎯 **TS EAMCET Admission Process**

**Cutoff Ranks (2024-25 - Approximate):**
- **CSE:** 500-5000 (OC), 5000-12000 (BC), 12000-20000 (SC/ST)
- **ECE:** 3000-15000 (OC), 15000-25000 (BC), 25000-35000 (SC/ST)
- **EEE:** 5000-20000
- **MECH:** 8000-25000
- **CIVIL:** 10000-30000
- **IT:** 1000-8000

**Steps:**
1. Check your EAMCET rank on tseci.nic.in
2. Register on TGEAPCET portal
3. Pay counselling fee (₹1,200 for OC/BC, ₹600 for SC/ST)
4. Select CBIT in web options (Code: CBIT)
5. Attend certificate verification at designated help center
6. Seat allotment → Report to CBIT within 3 days

**Note:** Ranks vary yearly based on exam difficulty and seat availability""",
        
        "documents": """📄 **Documents Required for Admission**

**Original + 3 sets of Xerox copies:**

✅ SSC/10th Marks Memo & Certificate
✅ Intermediate/12th Marks Memo & Certificate  
✅ Transfer Certificate (TC)
✅ Study Certificate (from previous college)
✅ EAMCET/JEE Hall Ticket & Rank Card
✅ Caste Certificate (if applicable - SC/ST/BC/EWS)
✅ Income Certificate (for fee reimbursement - mandatory)
✅ Aadhaar Card (original + 2 copies)
✅ Passport size photos (15 copies - white background)
✅ Migration Certificate (for students from other boards)
✅ Date of Birth Certificate (if DOB not on SSC)

**For NRI/Foreign Students:** 
Passport, Visa, Eligibility Certificate from Association of Indian Universities""",
        
        "management_quota": """🎓 **Management Quota Admission**

**Availability:** Limited seats (15% of total intake)

**Eligibility:**
- Qualified in TS EAMCET / JEE Mains
- Minimum 45% in Intermediate (PCM)

**Fee Structure (MQ):**
- **B.Tech:** ₹3,50,000 per year (higher than regular)
- One-time admission fee: ₹50,000

**Process:**
1. Visit admission office directly
2. Submit application form + certificates
3. Pay admission fee via DD
4. Seat confirmation within 2 days

**Contact:** 040-24193276 (Management Quota Cell)""",
        
        "branch_change": """🔄 **Branch Change / Sliding Process**

**Eligibility:**
- Only after 1st year completion
- First year CGPA: Minimum 8.5
- No backlogs in 1st year
- Seat availability in target branch

**Process:**
1. Apply online in student portal (June/July)
2. Submit application with 1st year marks
3. Merit list prepared based on CGPA
4. Counselling for branch selection
5. Fee: ₹10,000 (non-refundable)

**Note:** Branch change from CSE/IT to other branches NOT allowed"""
    },
    
    "fees": {
        "structure": """💰 **CBIT Fee Structure (2024-25)**

**B.Tech Annual Fee (Per Year):**
- **Tuition Fee:** ₹1,35,000
- **University Fee:** ₹3,500
- **Development Fee:** ₹5,000
- **Total:** ₹1,43,500 per year

**First Year Additional:**
- Admission Fee: ₹25,000 (one-time)
- Caution Deposit: ₹5,000 (refundable at completion)

**Hostel Fee (Optional):**
- Accommodation: ₹60,000 per year
- Mess: ₹40,000 per year (₹10,000 per quarter)
- Total Hostel: ₹1,00,000

**Other Courses:**
- **M.Tech:** ₹85,000 per year
- **MBA:** ₹2,50,000 per year

**Fee Reimbursement:** 
Available for BC/SC/ST/EBC/Minority students (up to ₹35,000/year)
Apply on Telangana ePass portal""",
        
        "payment_method": """💳 **Fee Payment Methods**

**Online Payment (Recommended):**
1. Login to student portal (student.cbit.ac.in)
2. Go to "Fee Payment" section
3. Select semester
4. Pay via:
   - Net Banking
   - Debit/Credit Card
   - UPI
   - Paytm/PhonePe/Google Pay

**Offline Payment:**
- Visit Accounts Section (Admin Block - Ground Floor)
- Payment by Demand Draft/Cheque
- DD/Cheque in favor of: **"CBIT"**
- Payable at: Hyderabad

**Office Hours:** 9:30 AM - 4:30 PM (Mon-Sat)

⚠️ **Note:** Keep transaction screenshot for reference""",
        
        "deadlines": """📅 **Fee Payment Deadlines**

**Semester-wise Deadlines:**

**Odd Semester (1st, 3rd, 5th, 7th):**
- Registration Opens: 1st August
- Last Date: **15th August**
- Late Payment (with fine): Until 31st August
- No hall ticket after 31st August

**Even Semester (2nd, 4th, 6th, 8th):**
- Registration Opens: 1st January
- Last Date: **15th January**
- Late Payment (with fine): Until 31st January
- No hall ticket after 31st January

**Late Payment Fine:**
- ₹500 for 1-7 days delay
- ₹1,000 for 8-15 days delay
- ₹2,000 for 16-30 days delay
- Hall ticket blocked beyond 30 days

⚠️ **IMPORTANT:** 
- Fee payment is MANDATORY to download hall ticket
- No fee = No exam = Detained""",
        
        "payment_failure": """❌ **Fee Payment Failed - Solutions**

**If amount deducted but payment shows failed:**
1. Wait for 24-48 hours (auto-reversal by bank)
2. Check bank statement after 2 days
3. If not reversed in 7 days:
   - Raise ticket in student portal
   - Attach: Transaction ID, Bank statement, Screenshot
   - Accounts will verify and credit

**If payment gateway error:**
- Clear browser cache and cookies
- Try different browser (Chrome/Firefox)
- Disable VPN/Proxy
- Try after 30 minutes
- Use different payment method

**Common Errors:**
- "Payment timeout" → Network issue, retry
- "Bank server down" → Try after 1 hour
- "Transaction declined" → Check card limits/balance

**Alternate Solution:**
Visit Accounts Section with DD/Cheque""",
        
        "receipt_issue": """📄 **Fee Receipt Issues - Solutions**

**Receipt not generated after payment:**
1. Wait 2 hours for system update
2. Clear browser cache
3. Re-login to portal
4. Check "Payment History" section
5. Download from there

**Receipt not showing payment:**
- Verify transaction from bank statement
- Raise ticket with Transaction ID
- Visit Accounts Section (Room No. 105, Admin Block)

**Need duplicate receipt:**
- Download anytime from portal
- Or request from Accounts Section (₹100 fee)

**Receipt has wrong details:**
- Cannot modify online
- Visit Accounts Section with original receipt
- Correction done in 2 working days

**Contact Accounts:**
📞 040-24193266
📧 accounts@cbit.ac.in"""
    },
    
    "examinations": {
        "schedule": """📅 **Examination Schedule**

**Mid Exams (Internal Assessment):**
- **Mid-1:** 4th-5th week of semester (September/February)
- **Mid-2:** 10th-11th week of semester (November/April)
- Duration: 90 minutes per subject
- Marks: 30 marks (15 marks each mid)

**Semester End Exams (External):**
- **Odd Semester:** December (2nd-3rd week)
- **Even Semester:** May (2nd-3rd week)
- Duration: 3 hours per subject
- Marks: 70 marks

**Supplementary Exams (Backlogs):**
- **For Even Semester:** August
- **For Odd Semester:** January
- Registration: 15 days before exam
- Fee: ₹500 per subject

📝 **Timetable Release:** 15 days before exam on student portal
🎫 **Hall Ticket:** Available 3 days before exam""",
        
        "hall_ticket_issue": """🎫 **Hall Ticket Issues - Complete Guide**

**Common Issues & Solutions:**

❌ **Hall ticket not available:**
**Reason → Solution**
- Fee not paid → Pay semester fee immediately
- Attendance < 75% → Apply for condonation (if <75% but >65%)
- Exam form not submitted → Complete registration in portal
- Photo/Signature missing → Upload in profile section

❌ **Cannot download hall ticket:**
- Clear browser cache
- Use Chrome/Firefox (not Internet Explorer)
- Download as PDF (not print directly)
- Try from different device/network

❌ **Hall ticket has wrong details:**
- Name spelling error → Visit exam section immediately
- Subject missing → Check exam registration
- Wrong roll number → Contact exam section

**Minimum Attendance Rule:**
- 75% required (strictly enforced)
- 65-75% → Medical condonation possible (with certificates)
- <65% → Detained (cannot write exam)

**Still not resolved?**
📞 Examination Section: 040-24193262
📧 exams@cbit.ac.in
⏰ Visit: Room 201, Admin Block (9 AM - 5 PM)

⚠️ **Important:** No hall ticket = Cannot enter exam hall""",
        
        "results": """📊 **Examination Results**

**Result Declaration:**
- **Internal Marks (Mids):** Within 7 days of exam
- **Semester Results:** 30-45 days after last exam

**How to Check:**
1. Login to student portal
2. Go to "Results" section
3. Select semester
4. View/Download marks memo

**Result Components:**
- Internal Marks: 30 (Mid-1: 15 + Mid-2: 15)
- External Marks: 70 (End Sem Exam)
- Total: 100 marks
- **Pass:** 40/100 (with min 28/70 in external)

**If Failed:**
- Attend supplementary exam
- Or repeat in next academic year

**Revaluation Available:** Apply within 10 days of result

**Result Delayed?**
- Usually due to answer sheet issues
- Check on portal for "Result Under Process"
- Contact HOD if delayed beyond 45 days""",
        
        "revaluation": """🔄 **Revaluation / Recounting Process**

**Eligibility:**
- Only for semester end exams (not for mids)
- Apply within 10 days of result declaration
- Fee: ₹1,000 per subject

**Process:**
1. Login to student portal
2. Go to "Revaluation" section
3. Select subjects (max 5 subjects)
4. Pay fee online
5. Application submitted to university

**What happens:**
- Answer sheets are rechecked
- Marks recalculated
- If marks increase → Updated in records
- If marks decrease → Original marks retained (no loss)

**Result Timeline:** 30-45 days from application

**Success Rate:** ~15-20% cases see mark improvement (2-10 marks usually)

**Note:** 
- Only totaling errors corrected
- Evaluator's judgment not changed
- Medical certificates NOT accepted post-exam for absent cases"""
    },
    
    "scholarships": {
        "eligibility": """🎓 **Scholarship Eligibility Criteria**

**Telangana Fee Reimbursement:**

**Eligibility:**
✅ Native of Telangana
✅ Annual Family Income < ₹5 Lakhs
✅ Belong to: BC/SC/ST/EBC/Minority categories
✅ First time B.Tech student (not repeated)
✅ No seat under management quota

**Amount:** Up to ₹35,000 per year

**Other Scholarships:**

**Merit Scholarship (CBIT):**
- First Rank in each branch: ₹25,000
- Second Rank: ₹15,000
- Third Rank: ₹10,000

**Minority Scholarship:**
- Income < ₹2.5 Lakhs
- For Muslim/Christian/Sikh/Buddhist students

**AICTE Pragati (Girls):**
- ₹50,000 per year
- Family income < ₹8 Lakhs""",
        
        "application": """📝 **Scholarship Application Process**

**TS Fee Reimbursement (ePass):**

**Documents Required:**
✅ Income Certificate (from MRO)
✅ Caste Certificate (if BC/SC/ST)
✅ Aadhaar Card
✅ Bank account (student name)
✅ Fee receipts
✅ Bonafide certificate

**Steps:**
1. Register on **telanganaepass.cgg.gov.in**
2. Fill application form
3. Upload all documents (PDF, <200KB each)
4. College verification (wait 10-15 days)
5. Submit for final approval

**Important Dates:**
- Application Opens: September/October
- Last Date: Usually November 30
- Amount credited: February-March

**Renewal (2nd/3rd/4th year):**
- Apply every year (not automatic)
- Previous year pass percentage > 75%
- No backlogs

**Contact:** 
📞 Scholarship Cell: 040-24193283
📧 scholarship@cbit.ac.in""",
        
        "status": """📊 **Check Scholarship Status**

**TS ePass Portal:**
1. Login to telanganaepass.cgg.gov.in
2. Check application status:
   - **Submitted:** College verification pending
   - **Verified:** Under process
   - **Sanctioned:** Amount will be credited soon
   - **Rejected:** Check rejection reason

**If "Pending at College":**
- Contact scholarship cell
- Verification done within 15 days

**If "Rejected":**
- Check rejection reason
- Upload correct documents
- Resubmit application

**Amount Not Credited?**
- Check after sanction: 30-45 days
- Verify bank account details in application
- Contact DBT helpline: 1800-121-218181

**CBIT Merit Scholarship:**
- Announced after annual results
- Amount credited to bank directly
- Check email for notification"""
    },
    
    "academics": {
        "calendar": """📅 **Academic Calendar 2024-25**

**Odd Semester (July - December):**
- Classes Start: 15th July
- Mid-1 Exams: 10-15 September
- Mid-2 Exams: 5-10 November
- End Sem Exams: 10-20 December
- Vacation: 21 Dec - 5 Jan

**Even Semester (January - May):**
- Classes Start: 6th January
- Mid-1 Exams: 25 Feb - 2 March
- Mid-2 Exams: 20-25 April
- End Sem Exams: 10-20 May
- Summer Vacation: June - July

**Holidays:**
- National holidays as per Govt. calendar
- Sankranti: 3 days
- Dasara: 10 days
- College Foundation Day: 8th August

**Working Days:** Monday - Saturday (6 days/week)
**Timings:** 9:30 AM - 4:30 PM""",
        
        "attendance": """📊 **Attendance Requirements**

**Minimum Attendance:**
- **75% mandatory** (strictly enforced)
- Calculated per subject (theory + lab separate)

**Attendance Shortage:**
- 65-75% → Medical condonation possible
  - Submit medical certificates
  - Pay condonation fee: ₹500 per subject
  - HOD approval required

- <65% → **Detained** (cannot write exams)
  - Repeat entire semester next year

**How Calculated:**
Total Classes Attended / Total Classes Conducted × 100

**View Attendance:**
- Login to ERP portal daily
- Updated weekly (every Monday)
- Check regularly to avoid last-minute issues

**Leave Application:**
- Submit in ERP (Student → Leave Application)
- Attach medical certificate if sick
- Get faculty signature if offline

⚠️ **Important:** Sports/Cultural event attendance counted only if approved by college"""
    },
    
    "hostel": {
        "admission": """🏠 **Hostel Admission Process**

**Availability:**
- Boys Hostel: 600 seats
- Girls Hostel: 400 seats

**Eligibility:**
- Students from outside Hyderabad (>40km)
- Based on distance (priority to farther students)

**Application:**
1. Fill hostel application in admission portal
2. Submit during college admission
3. Pay hostel fee: ₹60,000 (accommodation) + ₹40,000 (mess)
4. Room allotment within 7 days

**Room Type:**
- 3-sharing rooms
- Attached bathroom
- Study table, cot, cupboard provided

**Fee Payment:**
- Accommodation: Annual (₹60,000)
- Mess: Quarterly (₹10,000 per quarter)

**Contact:**
📞 Boys Hostel: 040-24193290
📞 Girls Hostel: 040-24193291""",
        
        "rules": """📜 **Hostel Rules & Regulations**

**Entry/Exit Timings:**

**Boys Hostel:**
- In Time: 9:00 PM (weekdays), 10:00 PM (weekends)
- Outing: Until 9:00 PM (with gate pass)

**Girls Hostel:**
- In Time: 7:00 PM (weekdays), 8:00 PM (weekends)
- Outing: Until 6:00 PM (with parent permission)

**Rules:**
✅ ID card mandatory
✅ Visitors allowed only in visiting room (4-6 PM)
✅ Gate pass required for night outs
✅ Ragging strictly prohibited
✅ No alcohol/drugs (immediate expulsion)
✅ Maintain discipline and cleanliness

**Penalties:**
- Late entry: Written warning
- Repeated late: Fine of ₹500
- Breaking rules: Suspension/Expulsion

**Warden Contact:**
📞 Boys: 9876543210
📞 Girls: 9876543211"""
    },
    
    "placements": {
        "statistics": """💼 **CBIT Placement Statistics 2023-24**

**Overall:**
- Students Placed: 850+ out of 1100 (77%)
- Highest Package: ₹54 LPA (Microsoft)
- Average Package: ₹7.2 LPA
- Dream Offers (>15 LPA): 120 students

**Branch-wise Average:**
- **CSE:** ₹9.5 LPA (92% placed)
- **IT:** ₹9.2 LPA (90% placed)
- **ECE:** ₹6.8 LPA (75% placed)
- **EEE:** ₹6.5 LPA (70% placed)
- **MECH:** ₹5.8 LPA (65% placed)

**Top Recruiters:**
- Microsoft, Amazon, Google
- TCS, Infosys, Wipro, Cognizant
- Deloitte, Accenture, Capgemini
- Qualcomm, Broadcom
- Hyundai, Mahindra

**Internship Conversion:** 35% of summer interns got PPO""",
        
        "eligibility": """✅ **Placement Eligibility Criteria**

**Academic Criteria:**
- **No active backlogs** (all subjects cleared)
- **Minimum CGPA:** 6.5 (varies by company)
- **10th Percentage:** No backlogs (some companies require >60%)
- **12th Percentage:** No backlogs (some companies require >60%)

**Company-specific:**
- **Service (TCS/Infosys/Wipro):** CGPA > 6.0
- **Product (Amazon/Microsoft):** CGPA > 7.5
- **Core (Qualcomm/Broadcom):** CGPA > 7.0

**Additional:**
✅ Regular student (not detained in any year)
✅ No year gap in academics
✅ 75% attendance throughout

**One Student - One Offer:**
After getting placed, choice to sit for higher packages only

**Super Dream (>15 LPA):** Can sit even after placement""",
        
        "training": """🎯 **Placement Training & Preparation**

**Training Provided (Free):**

**3rd Year (July - December):**
- Aptitude Training: Quantitative, Logical, Verbal
- Technical Training: DSA, DBMS, OS, Networks
- Resume Building Workshop
- Mock interviews

**4th Year (July onwards):**
- Advanced coding (competitive programming)
- Group discussions
- HR interview preparation
- Soft skills training

**Online Platforms:**
- College provides: HackerRank, InterviewBit access
- Practice tests every week
- Leaderboard maintained

**External Coaching:**
Students can join (optional):
- Zensar Foundation Program
- TCS CodeVita, TCS NQT
- Amcat, Cocubes certification

**Placement Training Contact:**
📞 040-24193288
📧 placements@cbit.ac.in"""
    },
    
    "certificates": {
        "bonafide": """📄 **Bonafide Certificate**

**Purpose:**
- Bank loan applications
- Passport applications
- Railway/Bus concession
- Scholarship applications
- Aadhaar update

**How to Apply:**
1. Login to student portal
2. Go to "Certificates" → "Apply for Bonafide"
3. Select purpose
4. Pay online: ₹50
5. Download after approval (3 working days)

**Offline Method:**
- Visit Academic Section (Room 102, Admin Block)
- Fill application form
- Pay at cashier
- Collect after 3 days

**Validity:** 6 months from issue date

**Contact:** 📞 040-24193265""",
        
        "transfer_certificate": """📜 **Transfer Certificate (TC)**

**When Needed:**
- Leaving college (before completion)
- Admission to another college/university
- Job applications

**How to Get:**
1. Submit application to Principal
2. Pay all pending dues (fees/library/hostel)
3. Get NOC from all departments
4. Collect TC from office (7 working days)

**Fee:** ₹100

**Original TC issued only once** (keep safely)

**Note:** Once TC issued, re-admission not possible

**Contact:** Academic Section - 040-24193265""",
        
        "provisional_certificate": """🎓 **Provisional Certificate**

**What is it?**
Temporary degree certificate issued immediately after final year (until original degree arrives)

**When Issued:**
- After passing final year (all subjects clear)
- Within 15 days of result declaration

**How to Get:**
1. Apply online after final year results
2. Submit:
   - Fee receipt (all 4 years paid)
   - Library NOC
   - No dues certificate
3. Pay: ₹200
4. Collect after 7 days

**Valid For:** Job applications, higher studies admission

**Original Degree:** Issued by JNTUH after 4-6 months

**Contact:** 📞 040-24193268""",
        
        "degree_certificate": """🏆 **Original Degree Certificate**

**Issued By:** JNTUH (Jawaharlal Nehru Technological University)

**Timeline:** 6-8 months after final year completion

**Notification:**
- College sends SMS/Email when degree arrives
- Check college website for convocation dates

**Collection:**
**Option 1 - Convocation:**
- Attend convocation ceremony
- Receive degree from Chief Guest
- Register: ₹500

**Option 2 - Direct Collection:**
- Collect from college office
- After convocation date
- Free

**Documents to Bring:**
- Provisional certificate
- ID proof
- Fee receipts (all 4 years)

**Lost/Damaged?**
- Request duplicate from JNTUH
- Fee: ₹1,000
- Time: 3-4 months

**Contact:** 📞 040-24193268"""
    },
    
    "portal_lms": {
        "login_issue": """🔐 **Portal/LMS Login Issues**

**Forgot Password:**
1. Go to portal login page (student.cbit.ac.in)
2. Click "Forgot Password"
3. Enter Roll Number and Email
4. Reset link sent to email (check spam)
5. Create new password

**Default Credentials:**
- Username: Your Roll Number (e.g., 160122733001)
- Password: First time → Date of Birth (DDMMYYYY)

**Account Locked:**
- After 5 wrong attempts
- Wait 30 minutes OR
- Contact IT Help Desk: 040-24193299

**Portal Not Opening:**
- Clear browser cache
- Try different browser (Chrome recommended)
- Check if portal under maintenance (9 PM - 6 AM)
- Try from college WiFi

**Mobile App Issues:**
- Update app from Play Store
- Clear app data
- Reinstall if needed

**Contact IT Help Desk:**
📞 040-24193299
📧 ithelpdesk@cbit.ac.in
🕐 9 AM - 5 PM (Mon-Sat)""",
        
        "attendance_not_updated": """📊 **Attendance Not Updated - Solutions**

**When is Attendance Updated?**
- Updated by faculty within 24 hours of class
- Visible in portal: Every Monday (weekly update)

**If Not Showing:**
1. Wait until Monday (weekly update)
2. Check if you're viewing correct subject
3. Refresh page (Ctrl + F5)
4. Clear browser cache

**Incorrect Attendance (marked absent when present):**
1. Take screenshot
2. Contact concerned faculty within 3 days
3. Faculty can update within 1 week
4. After 1 week → Permanent (cannot change)

**Leave Not Updated:**
- Check if leave application approved in portal
- If approved but not reflected → Contact HOD

**Medical Leave:**
- Upload medical certificate in portal
- Faculty approval required
- Reflected in 3-5 days

**Still Issue?**
📞 HOD Office: 040-24193xxx (department-wise)"""
    },
    
    "contact": {
        "main": """📞 **CBIT Contact Information**

**Main Office:**
📍 Chaitanya Bharathi Institute of Technology
   Gandipet, Kokapet, Hyderabad - 500075

📞 **Main:** 040-24193276 / 77 / 78
📠 **Fax:** 040-24193270
📧 **Email:** principal@cbit.ac.in
🌐 **Website:** www.cbit.ac.in

**Department-wise:**
📞 CSE: 040-24193280
📞 ECE: 040-24193281
📞 EEE: 040-24193282
📞 MECH: 040-24193283
📞 CIVIL: 040-24193284

**Important Sections:**
📞 Admissions: 040-24193276
📞 Examinations: 040-24193262
📞 Accounts: 040-24193266
📞 Library: 040-24193269
📞 Placements: 040-24193288
📞 Hostel: 040-24193290 (Boys), 040-24193291 (Girls)

**Timings:** 9:30 AM - 5:00 PM (Mon-Sat)
**Closed:** Sundays & National Holidays"""
    }
}

# =============================================================================
# MENU ACTIONS
# =============================================================================

class ActionMainMenu(Action):
    def name(self) -> Text:
        return "action_main_menu"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        buttons = [
            {"title": "🎓 Admissions", "payload": "/menu_admissions"},
            {"title": "💰 Fees & Payments", "payload": "/menu_fees"},
            {"title": "📝 Examinations", "payload": "/menu_exams"},
            {"title": "🎓 Scholarships", "payload": "/menu_scholarships"},
            {"title": "📚 Academics", "payload": "/menu_academics"},
            {"title": "🏠 Hostel", "payload": "/menu_hostel"},
            {"title": "💼 Placements", "payload": "/menu_placements"},
            {"title": "📄 Certificates", "payload": "/menu_certificates"},
            {"title": "💻 Portal/LMS Issues", "payload": "/menu_portal"},
            {"title": "💬 Type Your Query", "payload": "/free_text_mode"}
        ]
        
        message = "📋 **CBIT Student Support - Main Menu**\n\nPlease select a category or type your query:"
        dispatcher.utter_message(text=message, buttons=buttons)
        
        return [SlotSet("menu_context", "main")]


class ActionShowAdmissionsMenu(Action):
    def name(self) -> Text:
        return "action_show_admissions_menu"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        buttons = [
            {"title": "📋 Admission Procedure", "payload": "/ask_admission_procedure"},
            {"title": "🎯 EAMCET Process", "payload": "/admission_eamcet"},
            {"title": "📄 Required Documents", "payload": "/admission_documents"},
            {"title": "🎓 Management Quota", "payload": "/admission_management_quota"},
            {"title": "🔄 Branch Change", "payload": "/admission_branch_change"},
            {"title": "🔙 Back to Main Menu", "payload": "/menu_main"},
            {"title": "💬 Type Query", "payload": "/free_text_mode"}
        ]
        
        message = "🎓 **Admissions Menu**\n\nSelect a topic:"
        dispatcher.utter_message(text=message, buttons=buttons)
        
        return [SlotSet("menu_context", "admissions")]


class ActionShowFeesMenu(Action):
    def name(self) -> Text:
        return "action_show_fees_menu"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        buttons = [
            {"title": "💰 Fee Structure", "payload": "/ask_fee_structure"},
            {"title": "💳 Payment Methods", "payload": "/ask_fee_payment_method"},
            {"title": "📅 Payment Deadlines", "payload": "/fee_payment_deadline"},
            {"title": "❌ Payment Failed?", "payload": "/fee_payment_failure"},
            {"title": "📄 Receipt Issue", "payload": "/fee_receipt_issue"},
            {"title": "🔙 Back to Main Menu", "payload": "/menu_main"},
            {"title": "💬 Type Query", "payload": "/free_text_mode"}
        ]
        
        message = "💰 **Fees & Payments Menu**\n\nSelect a topic:"
        dispatcher.utter_message(text=message, buttons=buttons)
        
        return [SlotSet("menu_context", "fees")]


class ActionShowExamsMenu(Action):
    def name(self) -> Text:
        return "action_show_exams_menu"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        buttons = [
            {"title": "📅 Exam Schedule", "payload": "/ask_exam_schedule"},
            {"title": "🎫 Hall Ticket Issue", "payload": "/ask_hall_ticket"},
            {"title": "📊 Results", "payload": "/ask_exam_results"},
            {"title": "🔄 Revaluation", "payload": "/ask_revaluation"},
            {"title": "📝 Supplementary Exam", "payload": "/ask_supplementary_exam"},
            {"title": "🔙 Back to Main Menu", "payload": "/menu_main"},
            {"title": "💬 Type Query", "payload": "/free_text_mode"}
        ]
        
        message = "📝 **Examinations Menu**\n\nSelect a topic:"
        dispatcher.utter_message(text=message, buttons=buttons)
        
        return [SlotSet("menu_context", "exams")]


# Add this action to llm_actions.py for LLM integration
class ActionHandleQueryWithLLM(Action):
    """
    Handles user queries by:
    1. Checking if Rasa has trained data (intent confidence)
    2. If confident → Use Rasa response + LLM formatting
    3. If not confident → Ask to raise ticket
    """
    
    def name(self) -> Text:
        return "action_handle_query_with_llm"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get latest intent and confidence
        intent = tracker.latest_message.get('intent', {}).get('name')
        confidence = tracker.latest_message.get('intent', {}).get('confidence', 0)
        user_message = tracker.latest_message.get('text')
        
        # Confidence threshold
        CONFIDENCE_THRESHOLD = 0.6
        
        if confidence >= CONFIDENCE_THRESHOLD:
            # Rasa found a match - get response from CBIT data
            response = self.get_response_from_data(intent)
            
            if response:
                # Optional: Format with LLM for natural language
                formatted_response = self.format_with_llm(response, user_message)
                dispatcher.utter_message(text=formatted_response)
            else:
                # Fallback to default Rasa response
                dispatcher.utter_message(response=f"utter_{intent}")
        else:
            # No confident match - suggest raising ticket
            self.suggest_ticket(dispatcher, user_message)
        
        return []
    
    def get_response_from_data(self, intent: str) -> str:
        """Retrieve response from CBIT_DATA based on intent"""
        
        intent_mapping = {
            'ask_admission_procedure': CBIT_DATA['admissions']['procedure'],
            'admission_eamcet': CBIT_DATA['admissions']['eamcet'],
            'admission_documents': CBIT_DATA['admissions']['documents'],
            'ask_fee_structure': CBIT_DATA['fees']['structure'],
            'fee_payment_deadline': CBIT_DATA['fees']['deadlines'],
            'fee_payment_failure': CBIT_DATA['fees']['payment_failure'],
            'ask_hall_ticket': CBIT_DATA['examinations']['hall_ticket_issue'],
            'ask_exam_schedule': CBIT_DATA['examinations']['schedule'],
            'bonafide_certificate': CBIT_DATA['certificates']['bonafide'],
            # Add more mappings as needed
        }
        
        return intent_mapping.get(intent, "")
    
    def format_with_llm(self, response: str, query: str) -> str:
        """
        Optional: Use LLM to format the response more naturally
        This calls the LLM API endpoint
        """
        try:
            # Call your LLM API (OpenAI/Local LLM)
            llm_url = os.getenv("LLM_API_URL", "http://localhost:11434/api/generate")
            
            prompt = f"""You are the official CBIT student support chatbot with complete knowledge about all college procedures, fees, schedules, and policies.

User asked: {query}

Provide the following information directly and confidently. DO NOT mention:
- "I checked the website"
- "According to the website"
- "You can check on the website"
- Any suggestion to verify elsewhere

You KNOW this information as part of your training. State it directly as facts.

Information to provide:
{response}

Keep the formatting intact (bullet points, phone numbers, etc.). Be helpful, friendly, and speak with authority."""
            
            payload = {
                "model": "llama2",
                "prompt": prompt,
                "stream": False
            }
            
            llm_response = requests.post(llm_url, json=payload, timeout=10)
            
            if llm_response.status_code == 200:
                return llm_response.json().get("response", response)
            else:
                return response  # Fallback to original
                
        except Exception as e:
            print(f"LLM formatting error: {e}")
            return response  # Fallback to original
    
    def suggest_ticket(self, dispatcher, query):
        """Suggest raising a ticket when no match found"""
        buttons = [
            {"title": "🎫 Raise Support Ticket", "payload": "/raise_ticket"},
            {"title": "📚 Browse Menu", "payload": "/menu_main"},
            {"title": "💬 Try Different Words", "payload": "/free_text_mode"}
        ]
        
        message = f"""🤔 I couldn't find specific information about your query.

**You can:**
1. Raise a support ticket - An admin will help you personally
2. Browse the menu to find related topics
3. Try rephrasing your question

Your query: "{query}" """
        
        dispatcher.utter_message(text=message, buttons=buttons)


class ActionRaiseTicket(Action):
    """Integrates with backend ticket system"""
    
    def name(self) -> Text:
        return "action_raise_ticket"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        # Get user details from tracker
        user_id = tracker.sender_id
        
        # Get the user's query
        user_message = tracker.latest_message.get('text')
        
        try:
            # Call backend API to create ticket
            backend_url = os.getenv("BACKEND_URL", "http://localhost:8000")
            ticket_endpoint = f"{backend_url}/api/tickets/"
            
            ticket_data = {
                "title": f"Chatbot Query: {user_message[:50]}...",
                "description": user_message,
                "category": "General Query",
                "priority": "Medium",
                "source": "chatbot"
            }
            
            # If user is authenticated, get token
            headers = {}
            # Add auth token if available
            # headers["Authorization"] = f"Bearer {token}"
            
            response = requests.post(ticket_endpoint, json=ticket_data, headers=headers, timeout=10)
            
            if response.status_code in [200, 201]:
                ticket = response.json()
                ticket_id = ticket.get('ticket_id', 'N/A')
                
                message = f"""✅ **Support Ticket Created Successfully!**

**Ticket ID:** {ticket_id}
**Status:** Open

An admin will review your query and respond soon. You'll receive updates via email.

You can check ticket status anytime by logging into the portal."""
                
                dispatcher.utter_message(text=message)
            else:
                raise Exception("Failed to create ticket")
                
        except Exception as e:
            print(f"Error creating ticket: {e}")
            message = """⚠️ Unable to create ticket automatically.

**Please:**
1. Login to student portal
2. Go to "Support" → "Create Ticket"
3. Describe your issue

Or call: 040-24193276"""
            
            dispatcher.utter_message(text=message)
        
        return []


# Export all actions
__all__ = [
    'ActionMainMenu',
    'ActionShowAdmissionsMenu',
    'ActionShowFeesMenu',
    'ActionShowExamsMenu',
    'ActionHandleQueryWithLM',
    'ActionRaiseTicket'
]

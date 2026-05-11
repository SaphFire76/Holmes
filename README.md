# Holmes: LLM-Powered Phishing Detection App

### What the software does
Holmes is a full-stack web application that uses a large language model to analyse emails and detect potential phishing threats. It evaluates the text, flags risks, and provides an explanation of why an email may be malicious, while keeping a saved history of all past scans.

### Who it is for
This system is designed for everyday internet users and professionals who want a fast and reliable second opinion on suspicious emails before clicking any links or downloading attachments.

### Core features implemented
* **Secure user authentication:** Registration and login.
* **AI Analysis:** Submit email text for AI phishing analysis. This provides a verdict, risk level and explanation.
* **Scan History:** View a historical dashboard of past scans. Search for past scans through the search page.
* **Organisation:** Rename saved past scans for better tracking. Delete older saved scans.
* **Visual Risk Indicators:** Easily identify low, medium, or high risk threats.

### How to access the software
* **Live Application:** [https://holmes-nine.vercel.app](https://holmes-nine.vercel.app)
* **Repository:** [Insert your GitHub Link here]

### How to use the software
1. Log in using the test details below or register.
2. On the dashboard, paste the suspicious email into the text box and enter.
3. Wait for the LLM to return the verdict, risk level and explanation.
4. From the sidebar, click on 'New Scan' to return to the main page of the dashboard to analyse another email.
5. Use the 'History' list in the sidebar to view your past scans.
6. Click the more button, ⋮, next to a past scan in the sidebar to rename or delete the scan.
7. Click on the 'Search History' bar in the sidebar to search for past scans.

### Test details
*You can create your own account, or use this seeded demo account:*
* **Email:** test@test.com
* **Password:** password

### Sample input for testing
**Phishing Email:**
```
From: noreply@g00gleacc.com (Note the zero in google)
Subject: Urgent: Suspicious sign-in attempt
Dear User,
Someone recently used your password to sign in to your account. We have blocked this login attempt. Please check your account activity and update your password immediately by clicking the link below:
[Verify Your Account Now]
Thank you,
The Goggle Security Team
If you do not click the link within 24 hours, your account will be permanently deactivated.
```
**Legitimate Email:**
```
Good morning,

11+ Exam Preparation Courses In May Half-Term📝
📚 You can view all available 5 day courses in May Half-Term here
Please note, each course has a limited number of spaces. In the summer, places are reserved very quickly and we are unable to provide more.

NEW Free 11 Plus Practice Paper 🆓
✍️ 11+ ISEB Common Pre-Test Mathematics Paper 6
Please note, each free practice paper is available for download from our website for one week only.

If you have any questions, or if you’d like to discuss your child’s 11 Plus preparation specifically, please feel free to email us directly: teamkeen@theexamcoach.tv

Best wishes,
The Exam Coach Team
```

### If running locally
To run this application on your own machine, you will need two terminal windows open, one for the backend and one for the frontend.

#### 1. Database Setup (MySQL)
* Ensure you have a MySQL server installed and running on your local machine.
* Open your preferred database tool (e.g., MySQL Workbench, MySQL Command Line) and connect to your local server.
* Open the `init.sql` file provided in the repository and execute the entire script. This will automatically create the `Holmes` database, switch to it, and build all required tables and stored procedures.

#### 2. Backend Setup (FastAPI)
* Navigate to the `backend` directory.
* **Environment Configuration:** You need to set up your local secrets. Copy the provided `.env.example` blueprint to create your actual `.env` file:
  * Mac/Linux: `cp .env.example .env`
  * Windows (Command Prompt): `copy .env.example .env`
* Open that new `.env` file in your editor and fill in your specific details:
  * Add your local MySQL password.
  * Generate a secure `SECRET_KEY` (instructions are inside the file).
  * Add your Google Gemini API key.
* Activate your virtual environment: 
  * Mac/Linux: `source .venv/bin/activate`
  * Windows: `.venv\Scripts\activate`
* Install dependencies: 
  ```bash
  pip install -r requirements.txt
  ```
* Start the development server (runs on http://localhost:8000): 
  ```bash
  fastapi dev main.py
  ```

#### 3. Frontend (React/Vite) Setup
* Navigate to the `frontend` directory.
* **Environment Configuration:** Copy the provided `.env.example` blueprint to create your actual `.env` file:
  * Mac/Linux: `cp .env.example .env`
  * Windows (Command Prompt): `copy .env.example .env`
* Open that new `.env` file in your editor and verify or update the API URL to point to your local backend:
  ```env
  VITE_API_URL=http://localhost:8000
  ```
* Install dependencies:
  ```bash
  npm install
  ```
* Start the development server:
  ```bash
  npm run dev
  ```

### Known limitations
* **Performance:** AI analysis can occasionally take up to 1 minute. Time may vary on local models depending on model size.
* **Security:** Stored emails are currently saved in plain text and are not yet encrypted.
* **Validation:** Strict input validations (e.g., strong password enforcement, minimum character limits for email analysis) were ignored in this version for easier testing.
* **Features:** Account management features, such as password resets and updating user profiles, are not yet implemented.
* **UI/UX:** The frontend prioritises core functionality and backend integration, therefore lacking visual polish.

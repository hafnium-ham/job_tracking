# AI-Powered Job Application Tracker

This project is a comprehensive tool for tracking job applications, designed to streamline the job-hunting process. It uses a local AI model via Ollama to automatically parse and extract key information from job postings from URLs, PDF files, or pasted text. The application features a modern web dashboard, a command-line interface, and an optional macOS shortcut for quickly saving jobs from your browser.

## Features

-   **Web Dashboard:** A clean, responsive dashboard to view all your applications, track statuses, and visualize your progress.
-   **AI-Powered Parsing:** Automatically extracts job title, company, description, salary, and more using local LLMs with Ollama. No data is sent to external services.
-   **Multiple Input Sources:** Add jobs from:
    -   URLs (e.g., LinkedIn, Indeed)
    -   PDF files
    -   Pasted text descriptions
-   **Visual Statistics:** An interactive Sankey chart shows your application journey from "Applied" to "Hired" or "Rejected".
-   **Status Tracking:** Easily update the status of each application (e.g., Applied, Interview Scheduled, Hired, Rejected).
-   **macOS Shortcut (Optional):** A global hotkey (`Cmd+Shift+K`) to instantly capture a job posting from the active Google Chrome tab.
-   **Command-Line Interface:** A powerful CLI for users who prefer working in the terminal to add, view, and manage jobs.

---

## Tech Stack

-   **Backend:** Python, Flask
-   **AI:** [Ollama](https://ollama.com/) for running local LLMs (e.g., Phi-3, Llama 3)
-   **Frontend:** HTML, CSS, JavaScript
-   **Data Visualization:** D3.js, d3-sankey
-   **Python Libraries:** Requests, PyPDF2, pynput

---

## Setup and Installation

### 1. Prerequisites

-   **Python 3.8+:** Make sure Python and `pip` are installed.
-   **Ollama:** You must have Ollama installed and running for the AI extraction to work.
    -   [Download Ollama here](https://ollama.com/).
    -   After installing, pull a model. A small, fast model like `phi3:mini` is recommended.
        ```bash
        ollama pull phi3:mini
        ```

### 2. Clone the Repository

```bash
git clone [https://github.com/hafnium-ham/job_tracking](https://github.com/hafnium-ham/job_tracking)
cd job_trackeing
```

### 3. Set Up a Virtual Environment

It's highly recommended to use a virtual environment.

```bash
# Create the virtual environment
python3 -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
.\venv\Scripts\activate
```

### 4. Install Dependencies

Install the required Python packages from `requirements.txt`.

```bash
pip install -r requirements.txt
```

---

## How to Run

You can interact with the application through the Web UI, the CLI, or the macOS shortcut.

### 1. Run the Web Server

The primary way to use the application is through the Flask web server.

```bash
flask run --port=5001
```

Now, open your web browser and navigate to `http://127.0.0.1:5001`.

-   **Dashboard:** `http://127.0.0.1:5001/`
-   **Add a New Job:** `http://127.0.0.1:5001/add`

### 2. Use the Command-Line Interface (CLI)

The `cli.py` script provides a full-featured terminal interface.

```bash
# Show all jobs
python3 cli.py show

# Add a new job from a URL
python3 cli.py add [https://www.linkedin.com/jobs/view/some-job-id](https://www.linkedin.com/jobs/view/some-job-id)

# Add a new job from a PDF
python3 cli.py add /path/to/your/job-description.pdf

# Update a job's status
python3 cli.py update

# Show application statistics
python3 cli.py stats
```

### 3. Use the macOS Shortcut Listener (Optional)

This script runs in the background and listens for a global hotkey to capture jobs directly from Google Chrome.

**First-Time Setup:**

You may need to grant accessibility permissions to your terminal or code editor for it to listen to global key presses and control Chrome.

-   Go to **System Settings > Privacy & Security > Accessibility**. Add and enable your Terminal/iTerm/VSCode.
-   Go to **System Settings > Privacy & Security > Automation**. Find your Terminal and ensure "Google Chrome" is checked.

**Run the Listener:**

```bash
python3 shortcut_listener.py
```

Leave this terminal window running. Now, whenever you are on a job posting page in Chrome, press `Cmd+Shift+K`, and the script will automatically process and save the job.

---

## Project Structure

The project is organized into a clean and modular structure:

```
.
├── cli.py                  # Command-line interface logic
├── job_tracker.py          # Main application logic (parsing, managing)
├── requirements.txt        # Python dependencies
├── server.py               # Flask web server and API routes
├── shortcut_listener.py    # macOS-specific hotkey listener
├── add_job.html            # HTML for the 'add job' page
├── dashboard.html          # HTML for the main dashboard
└── jobs.json               # Database file where jobs are stored (created on first run)
```

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

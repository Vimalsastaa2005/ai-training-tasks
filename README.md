# Cherrapunji Weather Report Automation

Automated weather reporter that fetches live weather conditions for Cherrapunji (Sohra), Meghalaya, India from the Open-Meteo API, prints a summary to the console, and sends an HTML email report via Gmail SMTP.

## Features

- **Open-Meteo API**: Fetches current temperature, humidity, feels-like temperature, wind speed, and precipitation without requiring an API key.
- **HTML Email Report**: Sends a formatted email report using Gmail SMTP with STARTTLS.
- **GitHub Actions Automation**: Automatically triggers daily at 7:00 AM IST (01:30 UTC) or manually on demand.

## Setup & Running Locally

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the script:
   ```bash
   python weather.py
   ```

## GitHub Actions Configuration

To enable automated email delivery via GitHub Actions:

1. Go to your GitHub repository: **Settings** > **Secrets and variables** > **Actions**.
2. Click **New repository secret** and add the following:
   - `GMAIL_USER`: The sender Gmail address
   - `GMAIL_APP_PASSWORD`: 16-character Google App Password
   - `RECIPIENT_EMAIL`: Recipient's email address

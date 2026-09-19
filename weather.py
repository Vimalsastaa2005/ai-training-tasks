#!/usr/bin/env python3
"""
weather_email.py
----------------
Fetches the current weather for Cherrapunji (Sohra), Meghalaya, India from the
Open-Meteo API, shows it in the terminal, and emails an HTML report through
Gmail SMTP (port 587 + STARTTLS).

Before running:
    pip install requests
Then run:
    python weather_email.py
"""

import os
import sys
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Load .env file if present (for local execution)
_env_file = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_env_file):
    with open(_env_file, "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))

# =====================================================================
# SECTION 1: YOUR SETTINGS
# Reads from environment variables (recommended for GitHub Actions Secrets & .env),
# with default fallbacks for general settings.
# =====================================================================
GMAIL_USER = os.getenv("GMAIL_USER", "balaramanperumal91@gmail.com")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", "sastaasastaa@gmail.com")
EMAIL_SUBJECT = os.getenv("EMAIL_SUBJECT", "Daily Weather Report \u2013 Cherrapunji, Meghalaya")

try:
    import requests
except ImportError:
    print("ERROR: The 'requests' library is not installed.")
    print("Install it with:  pip install requests")
    sys.exit(1)

# =====================================================================
# SECTION 3: FIXED SETTINGS (location, API, SMTP)
# =====================================================================
LATITUDE = 25.27          # Cherrapunji (Sohra) latitude
LONGITUDE = 91.72         # Cherrapunji (Sohra) longitude
API_URL = "https://api.open-meteo.com/v1/forecast"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# WMO weather codes -> human-readable text
WMO_CODES = {
    0: "Clear Sky",
    1: "Mainly Clear",
    2: "Partly Cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing Rime Fog",
    51: "Light Drizzle",
    53: "Moderate Drizzle",
    55: "Dense Drizzle",
    56: "Light Freezing Drizzle",
    57: "Dense Freezing Drizzle",
    61: "Slight Rain",
    63: "Moderate Rain",
    65: "Heavy Rain",
    66: "Light Freezing Rain",
    67: "Heavy Freezing Rain",
    71: "Slight Snow",
    73: "Moderate Snow",
    75: "Heavy Snow",
    77: "Snow Grains",
    80: "Slight Rain Showers",
    81: "Moderate Rain Showers",
    82: "Violent Rain Showers",
    85: "Slight Snow Showers",
    86: "Heavy Snow Showers",
    95: "Thunderstorm",
    96: "Thunderstorm with Slight Hail",
    99: "Thunderstorm with Heavy Hail",
}


# =====================================================================
# SECTION 4: FETCH WEATHER FROM OPEN-METEO
# =====================================================================
def get_weather():
    """Ask Open-Meteo for the current weather and return it as a simple dictionary."""
    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "current": "temperature_2m,apparent_temperature,relative_humidity_2m,"
                   "wind_speed_10m,precipitation,weather_code",
        "wind_speed_unit": "kmh",      # get wind speed in km/h
        "timezone": "Asia/Kolkata",
    }

    # --- Step 1: make the request (handles network problems) ---
    try:
        response = requests.get(API_URL, params=params, timeout=15)
        response.raise_for_status()    # raises an error for HTTP 4xx/5xx
    except requests.exceptions.Timeout:
        raise RuntimeError("The weather request timed out. Please try again.")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Network error: cannot reach Open-Meteo. Check your internet connection.")
    except requests.exceptions.HTTPError as err:
        raise RuntimeError(f"Open-Meteo returned an HTTP error: {err}")
    except requests.exceptions.RequestException as err:
        raise RuntimeError(f"Weather request failed: {err}")

    # --- Step 2: read the response (handles invalid/unexpected data) ---
    try:
        current = response.json()["current"]
        code = int(current["weather_code"])
        return {
            "temperature": float(current["temperature_2m"]),
            "feels_like": float(current["apparent_temperature"]),
            "humidity": float(current["relative_humidity_2m"]),
            "wind_speed": float(current["wind_speed_10m"]),
            "precipitation": float(current["precipitation"]),
            "weather_code": code,
            "condition": WMO_CODES.get(code, f"Unknown (code {code})"),
        }
    except (ValueError, KeyError, TypeError):
        raise RuntimeError("Invalid weather response received from Open-Meteo.")


# =====================================================================
# SECTION 5: SHOW THE REPORT IN THE TERMINAL
# =====================================================================
def print_report(w, today):
    print("=" * 50)
    print("  Cherrapunji Daily Weather Report")
    print("=" * 50)
    print(f"  Date          : {today}")
    print(f"  Temperature   : {w['temperature']:.1f}°C")
    print(f"  Feels Like    : {w['feels_like']:.1f}°C")
    print(f"  Humidity      : {w['humidity']:.0f}%")
    print(f"  Wind Speed    : {w['wind_speed']:.1f} km/h")
    print(f"  Precipitation : {w['precipitation']:.1f} mm")
    print(f"  Condition     : {w['condition']}  (WMO code {w['weather_code']})")
    print("=" * 50)


# =====================================================================
# SECTION 6: BUILD THE HTML EMAIL
# =====================================================================
def build_email(w, today):
    """Create the email message with a plain-text version and an HTML version."""
    rows = [
        ("Date", today),
        ("Temperature", f"{w['temperature']:.1f}°C"),
        ("Feels Like", f"{w['feels_like']:.1f}°C"),
        ("Humidity", f"{w['humidity']:.0f}%"),
        ("Wind Speed", f"{w['wind_speed']:.1f} km/h"),
        ("Precipitation", f"{w['precipitation']:.1f} mm"),
        ("Condition", w["condition"]),
    ]

    # Plain-text fallback (for email apps that can't show HTML)
    text_body = "Cherrapunji Daily Weather Report\n\n" + \
                "\n".join(f"{label}: {value}" for label, value in rows)

    # HTML table rows (alternating background colours)
    table_rows = ""
    for i, (label, value) in enumerate(rows):
        bg = "#f4f8fc" if i % 2 == 0 else "#ffffff"
        table_rows += f"""
        <tr style="background-color:{bg};">
          <td style="padding:12px 20px;color:#5a6472;font-size:14px;border-bottom:1px solid #e3e8ef;">{label}</td>
          <td style="padding:12px 20px;color:#1f2933;font-size:15px;font-weight:bold;text-align:right;border-bottom:1px solid #e3e8ef;">{value}</td>
        </tr>"""

    html_body = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background-color:#eef2f7;font-family:Segoe UI,Helvetica,Arial,sans-serif;">
  <table width="100%" cellspacing="0" cellpadding="0" style="background-color:#eef2f7;padding:24px 0;">
    <tr><td align="center">
      <table width="560" cellspacing="0" cellpadding="0"
             style="max-width:560px;width:100%;background-color:#ffffff;border:1px solid #dde3ea;border-radius:8px;overflow:hidden;">
        <tr>
          <td style="background-color:#1e5a8a;padding:26px 24px;text-align:center;">
            <div style="color:#ffffff;font-size:22px;font-weight:bold;">Cherrapunji Daily Weather Report</div>
            <div style="color:#cfe3f5;font-size:13px;margin-top:6px;">Cherrapunji (Sohra), Meghalaya, India</div>
          </td>
        </tr>
        <tr><td><table width="100%" cellspacing="0" cellpadding="0">{table_rows}
        </table></td></tr>
        <tr>
          <td style="padding:14px 24px;text-align:center;background-color:#f7f9fc;color:#7b8794;font-size:12px;">
            Data source: Open-Meteo (open-meteo.com)
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = EMAIL_SUBJECT
    msg["From"] = GMAIL_USER
    msg["To"] = RECIPIENT_EMAIL
    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))   # the last part is preferred by email apps
    return msg


# =====================================================================
# SECTION 7: SEND THE EMAIL THROUGH GMAIL SMTP (STARTTLS)
# =====================================================================
def send_email(msg):
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        raise RuntimeError(
            "GMAIL_USER and GMAIL_APP_PASSWORD must be set in your .env file or environment variables."
        )
    # Google shows App Passwords with spaces; remove them before logging in.
    password = GMAIL_APP_PASSWORD.replace(" ", "")

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
            server.ehlo()                                        # introduce ourselves
            server.starttls(context=ssl.create_default_context())  # switch to encrypted connection
            server.ehlo()                                        # introduce ourselves again (now encrypted)
            server.login(GMAIL_USER, password)                   # log in with the App Password
            server.sendmail(GMAIL_USER, RECIPIENT_EMAIL, msg.as_string())
    except smtplib.SMTPAuthenticationError:
        raise RuntimeError(
            "Gmail login failed. Make sure GMAIL_USER is correct and GMAIL_APP_PASSWORD is a valid "
            "Google App Password (2-Step Verification must be enabled on the account)."
        )
    except smtplib.SMTPException as err:
        raise RuntimeError(f"Email could not be sent (SMTP error): {err}")
    except (OSError, ssl.SSLError) as err:
        raise RuntimeError(f"Email could not be sent (network/connection error): {err}")


# =====================================================================
# SECTION 8: MAIN PROGRAM (runs everything in order)
# =====================================================================
def main():
    today = datetime.now().strftime("%d %B %Y")

    # 1) Get the weather
    print("Fetching weather for Cherrapunji from Open-Meteo...")
    try:
        weather = get_weather()
    except RuntimeError as err:
        print(f"\nERROR: {err}")
        sys.exit(1)

    # 2) Show it in the terminal
    print()
    print_report(weather, today)

    # 3) Build the email
    message = build_email(weather, today)

    # 4) Send it
    print("\nSending email through Gmail SMTP (STARTTLS)...")
    try:
        send_email(message)
    except RuntimeError as err:
        print(f"\nERROR: {err}")
        sys.exit(1)

    # 5) Success!
    print(f"\nWeather report successfully sent to {RECIPIENT_EMAIL}")


if __name__ == "__main__":
    main()
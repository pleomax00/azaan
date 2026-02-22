import requests
import time
import datetime
import pytz
import os
import argparse
import subprocess
import sys

# ==============================
# CONFIG
# ==============================
CITY = "Gurgaon"
COUNTRY = "India"
MADHAB = 1          # 1 = Hanafi
METHOD = 1          # Karachi method
TIMEZONE = "Asia/Kolkata"

CHECK_INTERVAL = 30  # seconds
# ==============================

# Resolve script directory safely
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Audio files
FAJR_AUDIO = os.path.join(SCRIPT_DIR, "var", "fajr.mp3")
AZAN_AUDIO = os.path.join(SCRIPT_DIR, "var", "azan.mp3")
SIREN_AUDIO = os.path.join(SCRIPT_DIR, "var", "siren.mp3")

tz = pytz.timezone(TIMEZONE)
played_today = set()
is_ramadan = False


# ------------------------------
# Audio Playback
# ------------------------------
def play_audio(file_path):
    print(f"Attempting to play: {file_path}")

    if not os.path.exists(file_path):
        print("❌ Audio file does not exist!")
        return False

    try:
        subprocess.run(
            ["ffplay", "-nodisp", "-autoexit", file_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        print("✅ Playback finished")
        return True
    except Exception as e:
        print("❌ Audio error:", e)
        return False


# ------------------------------
# Fetch Prayer Timings + Hijri
# ------------------------------
def fetch_timings():
    global is_ramadan

    today = datetime.datetime.now(tz).strftime("%d-%m-%Y")
    url = f"http://api.aladhan.com/v1/timingsByCity/{today}"

    params = {
        "city": CITY,
        "country": COUNTRY,
        "method": METHOD,
        "school": MADHAB
    }

    response = requests.get(url, params=params, timeout=10)
    data = response.json()

    if data["code"] != 200:
        raise Exception("Failed to fetch prayer times")

    hijri_month = data["data"]["date"]["hijri"]["month"]["number"]
    is_ramadan = (hijri_month == 9)

    print("✅ Prayer timings fetched")
    print(f"🌙 Hijri Month: {hijri_month}")
    print("🕌 Ramadan mode:", "ON" if is_ramadan else "OFF")

    return data["data"]["timings"]


# ------------------------------
# Build Daily Schedule
# ------------------------------
def build_schedule(timings):
    today = datetime.datetime.now(tz)
    schedule = {}

    for prayer in ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]:
        time_str = timings[prayer].split(" ")[0]
        hour, minute = map(int, time_str.split(":"))

        prayer_time = tz.localize(datetime.datetime(
            today.year, today.month, today.day,
            hour, minute
        ))

        schedule[prayer] = prayer_time

    return schedule


# ------------------------------
# Get Next Prayer
# ------------------------------
def get_next_prayer(schedule):
    now = datetime.datetime.now(tz)
    upcoming = [(name, t) for name, t in schedule.items() if t > now]

    if not upcoming:
        return None, None

    return min(upcoming, key=lambda x: x[1])


# ------------------------------
# Service Loop
# ------------------------------
def run_service():
    print("🕌 Azan service started...")
    timings = fetch_timings()
    schedule = build_schedule(timings)

    while True:
        try:
            now = datetime.datetime.now(tz)

            # Refresh daily at 00:01
            if now.hour == 0 and now.minute == 1:
                print("🔄 Refreshing prayer timings...")
                timings = fetch_timings()
                schedule = build_schedule(timings)
                played_today.clear()

            # Countdown display
            next_name, next_time = get_next_prayer(schedule)

            if next_name:
                remaining = next_time - now
                total_sec = int(remaining.total_seconds())
                hrs, rem = divmod(total_sec, 3600)
                mins, secs = divmod(rem, 60)

                print(
                    f"[{now.strftime('%H:%M:%S')}] "
                    f"Next: {next_name} in {hrs:02d}:{mins:02d}:{secs:02d}"
                )

            # Trigger prayers
            for prayer, prayer_time in schedule.items():

                if prayer in played_today:
                    continue

                diff = (now - prayer_time).total_seconds()

                if 0 <= diff < CHECK_INTERVAL:

                    print(f"🔊 {prayer} time reached")

                    # -------- FAJR SPECIAL --------
                    if prayer == "Fajr":
                        print("Playing FAJR special azan...")
                        play_audio(FAJR_AUDIO)

                    # -------- MAGHRIB --------
                    elif prayer == "Maghrib":
                        if is_ramadan:
                            print("🌙 Ramadan detected → Playing Iftar siren FIRST...")
                            play_audio(SIREN_AUDIO)

                            print("Playing Azan after siren...")
                            play_audio(AZAN_AUDIO)
                        else:
                            print("Playing Azan...")
                            play_audio(AZAN_AUDIO)

                    # -------- OTHER PRAYERS --------
                    else:
                        print("Playing Azan...")
                        play_audio(AZAN_AUDIO)

                    played_today.add(prayer)

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            print("❌ Error:", e)
            time.sleep(60)


# ------------------------------
# CLI Entry
# ------------------------------
def main():
    parser = argparse.ArgumentParser(description="Azan Service")
    parser.add_argument("--test-azan", action="store_true")
    parser.add_argument("--test-siren", action="store_true")
    parser.add_argument("--test-fajr", action="store_true")

    args = parser.parse_args()

    if args.test_fajr:
        print("🧪 Testing FAJR Azan...")
        sys.exit(0 if play_audio(FAJR_AUDIO) else 1)

    if args.test_azan:
        print("🧪 Testing Normal Azan...")
        sys.exit(0 if play_audio(AZAN_AUDIO) else 1)

    if args.test_siren:
        print("🧪 Testing Siren...")
        sys.exit(0 if play_audio(SIREN_AUDIO) else 1)

    run_service()


if __name__ == "__main__":
    main()

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BROKER = os.getenv("MQTT_BROKER", "hayasaka.takofaru.dpdns.org")
PORT = int(os.getenv("MQTT_PORT", 8883))
USERNAME = os.getenv("MQTT_USERNAME", "web_maggot")
PASSWORD = os.getenv("MQTT_PASSWORD", "NJkyX*L47EEpzzFd@1W#fIf@")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

TOPIC_SENSOR = "maggot/sensor/data"
TOPIC_STATUS = "maggot/status/fase"
TOPIC_STATUS_BATAS = "maggot/status/batas"
TOPIC_KONTROL = "maggot/kontrol/fase"
TOPIC_BATAS = "maggot/kontrol/batas"

MAX_POINTS = 100
SENSOR_LOG_INTERVAL_SECONDS = int(os.getenv("SENSOR_LOG_INTERVAL_SECONDS", 5))

_BASE = Path(__file__).parent
AUTH_DB_FILE = str(_BASE / "maggot_users.db")
REFRESH_SEC = 2

DEFAULT_PHASE_LIMITS = {
    "Fase Telur": {"tempMin": 28.0, "tempMax": 35.0, "humidMin": 60.0, "humidMax": 80.0},
    "Fase Larva": {"tempMin": 27.0, "tempMax": 30.0, "humidMin": 60.0, "humidMax": 80.0},
    "Fase Pupa": {"tempMin": 27.0, "tempMax": 30.0, "humidMin": 0.0, "humidMax": 40.0},
    "Fase Lalat": {"tempMin": 27.5, "tempMax": 37.5, "humidMin": 60.0, "humidMax": 70.0},
}

SYSTEM_PROMPT = (
    "You are a BSF (Black Soldier Fly) maggot farming expert with deep knowledge in entomology, "
    "organic waste management, and precision agriculture. "
    "Current farming phase: {fase}. Optimal temperature: {tempMin}-{tempMax}°C. "
    "Optimal humidity: {humidMin}-{humidMax}%. Day of phase: {hari_ke}. "
    "Analyze the correlation between: "
    "(1) feeding patterns - jenis dan berat pakan per tanggal, (2) environmental conditions - "
    "suhu dan kelembapan over time, and (3) maggot growth - berat maggot per tanggal. "
    "Identify trends, anomalies, and give specific, actionable recommendations to optimize "
    "maggot production and waste conversion efficiency for the current phase. "
    "IMPORTANT: ALWAYS respond in high-quality, natural Indonesian language (Bahasa Indonesia). "
    "Do NOT use literal translations, Chinese characters, or unnatural phrasing like 'di监itor' instead of 'dimonitor'. "
    "Use bullet points and bold text for readability. Keep it highly professional yet easily understood by farmers."
)

GROQ_COOLDOWN_SECONDS = 30
MAX_TEXT_FIELD_CHARS = 500
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+|any\s+|the\s+)?previous\s+instructions?",
    r"disregard\s+(all\s+|any\s+|the\s+)?previous\s+instructions?",
    r"forget\s+(all\s+|any\s+|the\s+)?previous\s+instructions?",
    r"\bsystem\s*:",
    r"\bdeveloper\s*:",
    r"\bassistant\s*:",
    r"\[inst\]",
    r"<<\s*sys\s*>>",
    r"</?\s*system\s*>",
]
PROMPT_CONTROL_CHARS = str.maketrans({
    "<": "",
    ">": "",
    '"': "",
    "{": "",
    "}": "",
    "`": "",
})

import os
import configparser

from dotenv import load_dotenv

load_dotenv()

config = configparser.ConfigParser()
config.read("config.ini")

LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("Channel_Access_Token")
LINE_CHANNEL_SECRET = os.environ.get("Channel_Secret")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

OPENAI_API_KEY = os.environ.get("OPENAI_API")

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.environ.get("GOOGLE_CSE_ID")

IMGUR_CLIENT_ID = config['imgur_api']['Client_ID']
IMGUR_CLIENT_SECRET = config['imgur_api']['Client_Secret']
album_id = config['imgur_api']['Album_ID']
API_Get_Image = config['other_api']['API_Get_Image']

INTERNAL_BLACKLIST_SET = {
    "0987654321", 
    "0911222333",
}

BLACKLIST_USERS = {
    "U05893ab5a753814f29b5feb91046050e",
    "U57d8a8e7bbc2aa06b53821a1693dd46d",
    ""
}
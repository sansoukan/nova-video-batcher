import os
import requests
from supabase import create_client, Client
from dotenv import load_dotenv
from supabase.lib.client_options import ClientOptions

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
COLOSSYAN_API_KEY = os.getenv("COLOSSYAN_API_KEY")
COLOSSYAN_SPEAKER_ID = os.getenv("COLOSSYAN_SPEAKER_ID")
NOVA_IMAGE_URL = os.getenv("NOVA_IMAGE_URL")
CALLBACK_URL = os.getenv("CALLBACK_URL", "https://nova-callback-clean.vercel.app/api/colossyan-callback")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY, options=ClientOptions(schema="public"))

def get_question():
    try:
        res = supabase.table("nova_questions")             .select("id, question_fr, video_question_fr")             .limit(100).execute()
        for row in res.data:
            if not row.get("video_question_fr"):
                return row
        print("✅ Toutes les questions ont déjà une vidéo.")
        return None
    except Exception as e:
        print("❌ Erreur Supabase :", str(e))
        return None

def create_avatar():
    print("🧍 Création avatar Nova...")
    avatar_res = requests.post(
        "https://app.colossyan.com/api/v1/assets/actors",
        headers={
            "Authorization": f"Bearer {COLOSSYAN_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "sourceFileUrl": NOVA_IMAGE_URL,
            "displayName": "Nova",
            "gender": "Female",
            "language": "fr"
        }
    )
    if avatar_res.status_code != 201:
        raise Exception(f"❌ Création avatar échouée : {avatar_res.text}")
    actor_id = avatar_res.json()["name"]
    print(f"✅ Avatar créé : {actor_id}")
    return actor_id

def send_video_request(question, actor_id):
    print("🎬 Envoi requête vidéo...")
    headers = {
        "Authorization": f"Bearer {COLOSSYAN_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "script": {
            "type": "text",
            "input": question["question_fr"]
        },
        "config": {
            "fluent": True,
            "pad_audio": False,
            "result_format": "mp4",
            "resolution": "1080p",
            "aspect_ratio": "16:9"
        },
        "actors": [
            {
                "actor_id": actor_id,
                "voice_id": COLOSSYAN_SPEAKER_ID,
                "voice_config": {
                    "style": "default",
                    "rate": 1.0
                },
                "avatar_settings": {
                    "scale": 1,
                    "position": "center"
                },
                "language_code": "fr"
            }
        ],
        "callback_url": CALLBACK_URL,
        "metadata": {
            "questionId": question["id"]
        }
    }

    response = requests.post("https://api.colossyan.com/v1/videos", headers=headers, json=payload)

    if response.status_code == 200:
        print("✅ Vidéo demandée avec succès.")
    else:
        print("❌ Erreur Colossyan :", response.status_code)
        print(response.text)

if __name__ == "__main__":
    q = get_question()
    if q:
        actor = create_avatar()
        send_video_request(q, actor)

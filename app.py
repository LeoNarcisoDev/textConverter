from flask import Flask, render_template, request, send_file
from gtts import gTTS
import requests
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

# 🔐 Sua chave da API da ElevenLabs
ELEVENLABS_API_KEY = 'sk_0f9941691b81a1d8243809eaf4f8096e0d55a64261027cfd'

# 🎙️ IDs de vozes por idioma
ELEVENLABS_VOICES = {
    "pt-br": {"female": "EXAVITQu4vr4xnSDxMaL", "male": "TxGEqnHWrfWFTfGW9XjX"},  # Substitua se necessário
    "en": {"female": "21m00Tcm4TlvDq8ikWAM", "male": "AZnzlk1XvdvUeBnXmlld"},
    "es": {"female": "zcAOhNBS3c14rBihAFp1", "male": "MF3mGyEYCl7XYWbV9V6O"}
}

DB_PATH = "conversoes.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS conversoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            texto TEXT,
            idioma TEXT,
            voz TEXT,
            arquivo TEXT,
            data TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.route('/', methods=['GET', 'POST'])
def index():
    audio_file = None
    selected_lang = 'pt-br'
    selected_voice = 'gtts'

    if request.method == 'POST':
        text = request.form['text']
        selected_lang = request.form.get('lang', 'pt-br')
        selected_voice = request.form.get('voice', 'gtts')

        if text.strip():
            filename = f"audio_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp3"
            path = os.path.join("static", "audios", filename)

            try:
                if selected_voice == 'gtts':
                    tts = gTTS(text, lang=selected_lang)
                    tts.save(path)
                else:
                    voice_id = ELEVENLABS_VOICES[selected_lang][selected_voice]
                    headers = {
                        "xi-api-key": ELEVENLABS_API_KEY,
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "text": text,
                        "model_id": "eleven_multilingual_v2",
                        "voice_settings": {
                            "stability": 0.5,
                            "similarity_boost": 0.7
                        }
                    }

                    response = requests.post(
                        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                        json=payload,
                        headers=headers
                    )

                    if response.status_code == 200:
                        with open(path, "wb") as f:
                            f.write(response.content)
                    else:
                        return f"Erro na ElevenLabs: {response.text}", 500

                audio_file = filename

                # Salva no banco
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute('INSERT INTO conversoes (texto, idioma, voz, arquivo, data) VALUES (?, ?, ?, ?, ?)', (
                    text[:100],
                    selected_lang,
                    selected_voice,
                    filename,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ))
                conn.commit()
                conn.close()

            except Exception as e:
                return f"Erro ao gerar áudio: {str(e)}", 500

    return render_template('index.html', audio_file=audio_file, selected_lang=selected_lang, selected_voice=selected_voice)

@app.route('/download/<filename>')
def download(filename):
    return send_file(os.path.join("static", "audios", filename), as_attachment=True)

@app.route('/historico')
def historico():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, texto, idioma, voz, arquivo, data FROM conversoes ORDER BY id DESC")
    registros = c.fetchall()
    conn.close()
    return render_template("historico.html", registros=registros)

if __name__ == '__main__':
    os.makedirs("static/audios", exist_ok=True)
    app.run(debug=False)

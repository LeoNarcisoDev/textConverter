from flask import Flask, render_template, request, send_file
from gtts import gTTS
import os
from datetime import datetime

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    audio_file = None
    if request.method == 'POST':
        text = request.form['text']
        if text.strip():
            tts = gTTS(text, lang='pt-br')
            filename = f"audio_{datetime.now().strftime('%Y%m%d%H%M%S')}.mp3"
            path = os.path.join("static", "audios", filename)
            tts.save(path)
            audio_file = filename
    return render_template('index.html', audio_file=audio_file)

@app.route('/download/<filename>')
def download(filename):
    return send_file(os.path.join("static", "audios", filename), as_attachment=True)

if __name__ == '__main__':
    os.makedirs("static/audios", exist_ok=True)
    app.run(debug=False)


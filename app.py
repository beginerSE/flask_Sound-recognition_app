from flask import Flask, render_template, request,send_file,after_this_request,make_response,jsonify,redirect, url_for, send_from_directory
import pandas as pd
import os
import ffmpeg
import wave
import base64
import requests
import httplib2
from googleapiclient import discovery
import datetime

#APIキーを設定
key = 'AI~~~'
 
# API URL
DISCOVERY_URL = ('https://{api}.googleapis.com/$discovery/rest?version={apiVersion}')

app = Flask(__name__)

UPLOAD_DIR = './uploads'
ALLOWED_EXTENSIONS = set(['m4a','mp3','wav',])
app.config['UPLOAD_FOLDER'] = UPLOAD_DIR


@app.route('/')
def hello():
    return render_template('index.html')

def allwed_file(filename):
    # .があるかどうかのチェックと、拡張子の確認
    # OKなら１、だめなら0
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

#APIの情報を返す関数
def get_speech_service():
    http = httplib2.Http()
    return discovery.build(
        'speech', 'v1', http=http, discoveryServiceUrl=DISCOVERY_URL, developerKey=key)

def transcribe_file(speech_file,num):
    """Transcribe the given audio file."""

    with open(speech_file, 'rb') as audio_file:
        content = base64.b64encode(audio_file.read())

    if speech_file.encode == 'flac':
        encode_type = 'FLAC'
    elif speech_file.encode == 'wav':
        encode_type = 'LINEAR16'
    elif speech_file.encode == 'ogg':
        encode_type = 'OGG_OPUS'
    elif speech_file.encode == 'amr':
        encode_type = 'AMR'
    elif speech_file.encode == 'awb':
        encode_type = 'AMR_WB'
    else:
        encode_type = 'LINEAR16'
    service = get_speech_service()
    service_request = service.speech().recognize(
        body={
            'audio': {
                'content': content.decode('UTF-8')
            },
            'config': {
                'encoding': encode_type,
                'sampleRateHertz': 48000,
                'languageCode': 'ja-JP',
            },
        })
    response = service_request.execute()
    print('res', response)
    result_list=[]
    for result in response['results']:

        result_list.append(result['alternatives'][0]['transcript'])

    return result_list

@app.route('/result', methods=['POST'])
def uploads_file():

    # リクエストがポストかどうかの判別
    if request.method == 'POST':
        # ファイルがなかった場合の処理
        if 'file' not in request.files:
            make_response(jsonify({'result':'uploadFile is required.'}))

        # データの取り出し
        file = request.files['file']

        # ファイル名がなかった時の処理
        if file.filename == '':
            make_response(jsonify({'result':'filename must not empty.'}))


        # ファイルのチェック
        if file and allwed_file(file.filename):

            filename = file.filename

            # ファイルの保存
            file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))

            stream = ffmpeg.input("uploads/" + filename)
            now = datetime.datetime.now()
            s = now.strftime("%Y%m%d_%H%M%S")
            stream = ffmpeg.output(stream, f'output_{s}.wav')
            ffmpeg.run(stream)

            wfile = wave.open(f'output_{s}.wav', "r")
            frame_rate = wfile.getframerate()
            print(frame_rate)
            result_list = transcribe_file(f'output_{s}.wav',frame_rate)
            wfile.close()
            os.remove(f'output_{s}.wav')
            return render_template('result.html',result_list=result_list)
    return  

if __name__ == "__main__":
    app.run(debug=True)
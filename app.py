from flask import Flask, request, jsonify, render_template
from flask_cors import CORS # CORS 문제를 해결하기 위해 필요한 라이브러리입니다.
import requests
import json
import os # os 모듈은 파일 경로 등을 다룰 때 사용됩니다.

app = Flask(__name__)
# CORS 설정: 프론트엔드(웹사이트)와 백엔드(Flask 서버)가 다른 주소/포트에서 실행될 때 통신을 허용합니다.
# 개발 단계에서는 모든 Origin을 허용하지만, 실제 서비스에서는 웹사이트의 정확한 Origin(예: http://localhost:5500)으로 제한하는 것이 보안에 좋습니다.
CORS(app)

# --- 🚨 중요! 이 부분을 여러분의 네이버 API 정보로 수정해주세요 🚨 ---
# 1. 네이버 개발자 센터에서 발급받은 Client ID를 여기에 입력하세요.
NAVER_CLIENT_ID = "2tgiBdoOUQUrweAliewZ" # 예: "YOUR_CLIENT_ID"

# 2. 네이버 개발자 센터에서 발급받은 Client Secret을 여기에 입력하세요.
NAVER_CLIENT_SECRET = "TBsBshAYbS" # 예: "YOUR_CLIENT_SECRET"
# --- 설정 끝 ---

def search_naver_image(query, display_count=1):
    """
    네이버 검색 API를 사용하여 이미지 URL을 검색합니다.
    """
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        print("🚨 오류: NAVER_CLIENT_ID 또는 NAVER_CLIENT_SECRET이 설정되지 않았습니다.")
        return []

    url = "https://openapi.naver.com/v1/search/image" # 이미지 검색 API 엔드포인트
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    params = {
        "query": query,
        "display": display_count,
        "sort": "sim" # sim: 정확도순 (기본값), date: 날짜순
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status() # HTTP 오류 발생 시 예외 발생 (예: 401 Unauthorized, 404 Not Found 등)

        data = response.json()
        
        image_urls = []
        if 'items' in data:
            for item in data['items']:
                # 썸네일 이미지를 선호하는 경우 'thumbnail' 사용
                if 'thumbnail' in item:
                    image_urls.append(item['thumbnail'])
                # 원본 이미지를 선호하는 경우 'link' 사용 (더 큰 이미지일 수 있음)
                # elif 'link' in item:
                #     image_urls.append(item['link'])
        
        return image_urls

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP 오류 발생: {http_err}")
        print(f"응답 내용: {response.text}")
        return []
    except requests.exceptions.RequestException as req_err:
        print(f"네이버 이미지 검색 중 요청 오류 발생: {req_err}")
        return []
    except json.JSONDecodeError as json_err:
        print(f"JSON 디코딩 오류: {json_err}")
        print(f"잘못된 응답 내용: {response.text}")
        return []

# --- Flask 라우트 (웹 페이지 주소) 정의 ---

# 웹사이트의 메인 페이지를 보여주는 라우트
# 사용자가 http://127.0.0.1:5000/ 로 접속하면 이 함수가 실행됩니다.
@app.route('/')
def index():
    # 'templates' 폴더 안의 'index.html' 파일을 찾아서 사용자에게 보여줍니다.
    return render_template('index.html')

# 메뉴 이미지 요청을 받아서 처리하는 API 엔드포인트
# script.js에서 http://localhost:5000/get-menu-image?menu=갈비찜 처럼 요청을 보낼 때 이 함수가 실행됩니다.
@app.route('/get-menu-image', methods=['GET'])
def get_menu_image_endpoint():
    """
    프론트엔드에서 메뉴 이름을 받아 네이버 이미지 검색 API를 호출하고
    결과 이미지 URL을 반환하는 API 엔드포인트입니다.
    """
    # 프론트엔드에서 'menu'라는 쿼리 파라미터로 메뉴 이름을 받습니다.
    menu_name = request.args.get('menu')

    if not menu_name:
        # 메뉴 이름이 없으면 오류 응답을 보냅니다.
        return jsonify({"error": "메뉴 이름이 필요합니다. 'menu' 쿼리 파라미터를 포함해주세요."}), 400

    print(f"프론트엔드로부터 '{menu_name}' 이미지 요청을 받았습니다.")
    
    # 네이버 이미지 검색 함수를 호출하여 이미지 URL을 가져옵니다.
    image_urls = search_naver_image(menu_name, display_count=1) # 가장 첫 번째 이미지만 가져옵니다.

    if image_urls:
        # 이미지를 성공적으로 찾았으면 첫 번째 이미지 URL을 반환합니다.
        print(f"'{menu_name}' 이미지 URL: {image_urls[0]} 전송 완료.")
        return jsonify({"imageUrl": image_urls[0]}), 200
    else:
        # 이미지를 찾지 못했으면 오류 메시지를 반환합니다.
        print(f"'{menu_name}' 이미지를 찾을 수 없습니다.")
        return jsonify({"imageUrl": None, "message": "해당 메뉴의 이미지를 찾을 수 없습니다."}), 404

# --- Flask 서버 실행 ---
if __name__ == '__main__':
    # debug=True: 개발 중에 코드 변경 시 서버가 자동으로 재시작됩니다. (운영 환경에서는 False로 설정)
    # port=5000: 서버를 5000번 포트에서 실행합니다. (프론트엔드와 다른 포트 사용 권장)
    print("✨ Flask 백엔드 서버가 시작됩니다. ✨")
    print("웹 브라우저에서 'http://127.0.0.1:5000/' 로 접속하여 웹사이트를 확인하세요.")
    print("API 테스트: 'http://127.0.0.1:5000/get-menu-image?menu=갈비찜' 로 접속하여 테스트할 수 있습니다.")
    app.run(debug=True, port=5000)
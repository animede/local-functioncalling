from datetime import datetime
from time import sleep
import requests
import subprocess
import threading
import cv2





camera_thread=False
cap = None  # VideoCaptureオブジェクトをグローバルに

def get_weather(city_name):
    url = f"http://wttr.in/{city_name}?format=%l:+%c+%t+%h+%w"
    try:
        response = requests.get(url)
        response.raise_for_status()  # エラーチェック
        weather_info = response.text.strip()  # 天気情報を変数に保存
        return True, weather_info
    except requests.exceptions.HTTPError as http_err:
        return False, f"HTTPエラーが発生しました: {http_err}"
    except requests.exceptions.RequestException as err:
        return False, True, f"エラーが発生しました: {err}"

# camera スレッド
def get_camera_th():
    global camera_thread
    global cap

    while camera_thread:
        if cap is None or not cap.isOpened():
            print("カメラが初期化されていません。")
            break
        ret, camera_frame = cap.read()
        if not ret:
            print("カメラが使用できません")
            break
        try:
            cv2.imshow("camera thread1", camera_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        except Exception as e:
            print("camera is not ready", e)
        sleep(0.1)

    # メモリを解放して終了
    if cap:
        cap.release()
        cap = None  # capオブジェクトを再度使えるようにリセット
    cv2.destroyAllWindows()
    
def execfunction(json_data):
    #return では　返す値の最初が、メッセージに意味があるかどうか　ある＝True, なし=False
    #例えば何らかの操作をして結果がメッセージにある、エラーの説明がある場合などは　　ある＝True,
    #操作をしたが操作後のメッセージがない場合は　なし=False
    function=json_data['function']
    print("function=",function)
    
    #　年日時分を答える    
    if function=="get_current_date_time" or function=="get_current_date":
        if json_data['parameter1']=="time":
            answer = datetime.now().replace(second=0, microsecond=0).strftime("%H時%M分").lstrip("0").replace(" 0", " ")
        elif json_data['parameter1']=="date":
            answer = datetime.now().strftime("%m月%d日").lstrip("0").replace(" 0", " ")
        elif json_data['parameter1']=="year":
            answer = datetime.now().strftime("%Y年")
        result=True
        print(str(answer))
        return result, True, str(answer)

    #　カメラのon/off
    if function=="camera":
        global camera_thread
        global cap
        param=json_data['parameter']
        if param=="open":
            if not camera_thread:
                # カメラがスタートしていない場合のみ、カメラとスレッドを開始
                camera_thread = True
                cap = cv2.VideoCapture(0)  # カメラの初期化
                get_camera_th1 = threading.Thread(target=get_camera_th)
                get_camera_th1.start()
                answer="カメラオープン"
            
        elif param=="close":
            if camera_thread:
                # カメラが停止されていない場合のみ、カメラとスレッドを停止
                camera_thread = False
                sleep(1)  # スレッドが終了するまで待機
            answer="カメラクローズ"
        return True,True, answer

    #　天気
    if function=="get_weather":
        param=json_data['parameter']
        result, weather_in = get_weather(param)
        print("weather_in=",weather_in)
        result=True #成功
        message_conv=True #言い換える
        return result,message_conv, weather_in 
    
    #　画像の解析処理
    if function=="image_analysis":
        return True, True, "開発中のファンクションです"

    #　システムの操作
    if function=="sys-cont":
        param=json_data['parameter']
        param1=json_data['parameter1']
        if param1:
            param1=param1.replace(".","*.")
            result = subprocess.run([param , param1], capture_output=True, text=True)
        else:
            param_list = param.split(" ")
            result = subprocess.run(param_list, capture_output=True, text=True)
        output = result.stdout
        result=True #成功
        message_conv=False #言い換えはしない
        return result,message_conv, output 
    else:
        return True, True, "開発中のファンクションです"
        
        

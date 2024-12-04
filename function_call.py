import openai
from   openai import OpenAI
import requests
import json
import re
#from  def_function import functions,f_role,c_role
from  def_function_2B import functions,f_role,c_role

client = OpenAI(
    base_url="http://127.0.0.1:8080/v1",
    api_key="YOUR_OPENAI_API_KEY",  # このままでOK
    )

def chat_functioncalling(client,user_msg):

    role = f_role + str(functions)

    # ステップ1: ユーザー入力と関数の定義を GPT に送る
    messages = [{"role": "system", "content": role},{"role": "user", "content": user_msg}]
    completion = client.chat.completions.create(
        model="gemma2:latest",
        messages=messages,
    )
    print(completion)
    out1=completion.choices[0].message.content
    print("out1=",out1)
    
    # JSON部分を抽出
    match = re.search(r'\{(.|\s)*?\}', out1)
    if match:
        # 抽出したJSON文字列を取得し、特殊な引用符や文字変換
        json_str = match.group(0)
        json_str = json_str.replace("「", '"').replace("」", '"')  # 日本語のカギカッコを標準のダブルクオートに
        json_str = json_str.replace("'", '"')  # シングルクオートをダブルクオートに変換
        json_str = json_str.replace("“", '"').replace("”", '"')
        json_str = json_str.replace("‘", '"').replace("’", '"')
        json_str = json_str.replace("None", 'null')
        json_str = json_str.replace(",}", '}')
        # JSONデータに変換
        try:
            json_data = json.loads(json_str)
        except json.JSONDecodeError:
            json_data={"function":'none'}
        message=out1.strip()
    else:
        json_data={"function":'none'}
        message=out1.strip()
    if json_data!={"function":'none'}:
        function_name =  json_data["function"]
        try:
            param=json_data["parameter"]
        except:
            param="none"
        try:
            param1=json_data["parameter1"]
        except:
            param1="none"
        try:
            param1=json_data["parameter2"]
        except:
            param1="none"

    message=re.sub(r"\{.*?\}\s*", "", message).strip()
    return json_data,message

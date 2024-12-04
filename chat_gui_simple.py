import asyncio
from fastapi import FastAPI, Form, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from openai import AsyncOpenAI,OpenAI
import json
from function_call import chat_functioncalling
from exec_func import execfunction
app = FastAPI()

client = AsyncOpenAI(
    #base_url="http://localhost:8080/v1",
    base_url='http://192.168.5.71:8080/v1',
    api_key="YOUR_OPENAI_API_KEY",  # このままでOK
)

fc_client = OpenAI(
    #base_url="http://localhost:8080/v1",
    base_url='http://192.168.5.71:8080/v1',
    api_key="YOUR_OPENAI_API_KEY",  # このままでOK
)

# 接続管理のためのクラス
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@app.get("/", response_class=HTMLResponse)
async def get():
    with open('static/index.html', 'r') as f:
        return f.read()

@app.post("/fc")
def function_calling(input_text: str = Form(...)):
    
    json_data, message = chat_functioncalling(fc_client,input_text)
    function=json_data["function"]

    if function=='none' or json_data=={} :
        function="none"
        result=False
        message="***実行できる関数はありません"
        message_conv=True
    else:
        result,message_conv,message = execfunction(json_data)
        print("***result=",result,"***message=",message)
        if message_conv:
            message= "以下を丁寧に言い換えてください。\n"+message
            message_conv=True
        else:
            message=message
            message_conv=False

    return {"fresul":result, "message": message,"message_conv":message_conv, "function":function, "json_data":json_data}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            data_dict = json.loads(data)  # 受信したJSONデータをPython辞書に変換
            message = data_dict.get("message")
            role = data_dict.get("role")
            print(f"Received message: {message} with role: {role}")
            stream = await client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": role, "content": message}],
                stream=True
            )
            response_sum = ""
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    response_sum += chunk.choices[0].delta.content or ""
                    chunk_data = chunk.choices[0].delta.content
                    await manager.send_personal_message(chunk_data, websocket)
                print("chunk sum  ==>", response_sum)
            print("+++++++++++++++++++++++++++++++++++++")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Client disconnected")
    except Exception as e:
        manager.disconnect(websocket)
        print(f"Error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)



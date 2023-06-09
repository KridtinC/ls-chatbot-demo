from flask import Flask, request, abort
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
from llama_index import SimpleDirectoryReader, GPTListIndex, GPTVectorStoreIndex, LLMPredictor, PromptHelper, StorageContext, load_index_from_storage
import os
import openai
import dotenv

config = dotenv.dotenv_values(".env")
openai.api_key = config['OPENAI_API_KEY']
os.environ["OPENAI_API_KEY"] = config['OPENAI_API_KEY']

storage_context = StorageContext.from_defaults(persist_dir="storage")
index = load_index_from_storage(storage_context)
q_engine = index.as_query_engine(response_mode="compact")

app = Flask(__name__)

line_bot_api = LineBotApi(config['OA_CHANNEL_ACCESS_TOKEN'])
handler = WebhookHandler(config['OA_CHANNEL_SECRET'])

@app.route("/health", methods=['GET'])
def health():
    return 'OK'

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    resp = q_engine.query(event.message.text).response
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=resp.strip('\n')))

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug = True)
from PyAissistant import DeepSeekBot
from flask import Flask, request

app = Flask(__name__)


@app.route('/')
def index():
    return 'Flask SSE Example'


@app.route('/chat', methods=['GET'])
def chat():
    # 获取URL中的msg参数
    msg = request.args.get('msg')
    bot = DeepSeekBot()
    bot.stream = False
    response_text = bot.chat(msg)
    print('*****' + response_text + '-----')
    return response_text


if __name__ == '__main__':
    app.run(debug=True)

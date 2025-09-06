# from flask import Flask, Response, render_template
#
# app = Flask(__name__)
#
# @app.route("/")
# def index():
#     return render_template("index.html")
#
# @app.route("/focus-translator-stream")
# def stream():
#     def event_stream():
#         import time
#         counter = 0
#         while True:
#             counter += 1
#             yield f"data: 翻译结果 {counter}\n\n"
#             time.sleep(1)
#     return Response(event_stream(), mimetype="text/event-stream")
#
# if __name__ == "__main__":
#     app.run(debug=True)


from flask import Flask, Response, request, render_template
import queue
import time

app = Flask(__name__)

# 用于存储外部传入的翻译文本
message_queue = queue.Queue()


@app.route("/")
def index():
    return render_template("index.html")
@app.route("/push", methods=["POST"])
def push_message():
    """外部程序通过 POST 提交翻译内容"""
    text = request.form.get("text") or request.json.get("text")
    if text:
        message_queue.put(text)
        return {"status": "ok", "msg": text}
    return {"status": "error", "msg": "no text provided"}, 400


@app.route("/stream")
def stream():
    """前端通过 SSE 获取实时翻译流"""
    def event_stream():
        while True:
            try:
                # 等待新消息（5 秒超时，避免阻塞过久）
                msg = message_queue.get(timeout=5)
                yield f"data: {msg}\n\n"
            except queue.Empty:
                # 保持连接，防止超时断开
                yield ": keep-alive\n\n"
                time.sleep(0.1)

    return Response(event_stream(), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(debug=True, threaded=True)




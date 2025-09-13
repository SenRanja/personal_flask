from flask import Flask, Response, request, render_template
import queue
import threading

app = Flask(__name__)

# 保存所有订阅的客户端队列
subscribers = []
lock = threading.Lock()
# log filename
LOG_FILE = "messages.log"

def publish_message(msg):
    """广播消息到所有订阅者"""
    with lock:
        for q in subscribers:
            q.put(msg)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/push", methods=["POST"])
def push_message():
    text = request.form.get("text") or (request.json and request.json.get("text"))
    if text:
        publish_message(text)

        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(text + "\n")

        return {"status": "ok", "msg": text}
    return {"status": "error", "msg": "no text provided"}, 400

@app.route("/stream")
def stream():
    def event_stream(q):
        try:
            while True:
                msg = q.get()  # 阻塞直到有消息
                yield f"data: {msg}\n\n"
        except GeneratorExit:
            # 客户端断开时自动退出
            with lock:
                subscribers.remove(q)

    q = queue.Queue()
    with lock:
        subscribers.append(q)
    return Response(event_stream(q), mimetype="text/event-stream")

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, threaded=True)

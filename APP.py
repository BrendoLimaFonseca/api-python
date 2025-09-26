from flask import Flask, request, jsonify
from threading import Lock

app = Flask(__name__)
lock = Lock()
storage = []

MAX_ITEMS = 10
ALARM_THRESHOLD = 5


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    try:
        number = int(data.get("number"))
        name = str(data.get("name")).strip()
    except Exception:
        return jsonify({"ok": False, "msg": "Número inválido ou nome ausente."}), 400

    if name == "":
        return jsonify({"ok": False, "msg": "Nome vazio."}), 400

    with lock:
        for item in storage:
            if item["number"] == number:
                item["name"] = name
                count = len(storage)
                alarm = (count == ALARM_THRESHOLD)
                return jsonify({"ok": True, "msg": "Atualizado.", "count": count, "alarm": alarm})

        if len(storage) >= MAX_ITEMS:
            return jsonify({"ok": False, "msg": f"Limite de {MAX_ITEMS} atingido."}), 400

        storage.append({"number": number, "name": name})
        count = len(storage)
        alarm = (count == ALARM_THRESHOLD)
        return jsonify({"ok": True, "msg": "Cadastrado.", "count": count, "alarm": alarm})


@app.route("/search", methods=["GET"])
def search():
    numbers_param = request.args.get("numbers", "")
    if not numbers_param:
        return jsonify({"ok": False, "msg": "Parâmetro 'numbers' ausente."}), 400

    try:
        nums = [int(n.strip()) for n in numbers_param.split(",") if n.strip() != ""]
    except Exception:
        return jsonify({"ok": False, "msg": "Formato inválido para 'numbers'."}), 400

    with lock:
        results = []
        index = {item["number"]: item["name"] for item in storage}
        for n in nums:
            results.append({"number": n, "name": index.get(n, None)})
        return jsonify({"ok": True, "results": results})


@app.route("/count", methods=["GET"])
def count():
    with lock:
        return jsonify({"count": len(storage)})


@app.route("/reset", methods=["POST"])
def reset():
    with lock:
        storage.clear()
        return jsonify({"ok": True, "msg": "Reset feito."})


@app.route("/all", methods=["GET"])
def get_all():
    with lock:
        return jsonify({"ok": True, "results": storage})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

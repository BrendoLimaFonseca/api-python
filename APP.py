from flask import Flask, request, jsonify
from threading import Lock
import json
import os

app = Flask(__name__)
lock = Lock()

storage = []

MAX_ITEMS = 10
ALARM_THRESHOLD = 5
DATA_FILE = "data.json"


def load_data():
    """Carrega os dados do arquivo JSON ao iniciar a API"""
    global storage
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                storage = json.load(f)
            except json.JSONDecodeError:
                storage = []


def save_data():
    """Salva os dados no arquivo JSON sempre que houver alteração"""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(storage, f, ensure_ascii=False, indent=2)


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
                save_data()
                count = len(storage)
                alarm = (count == ALARM_THRESHOLD)
                return jsonify({"ok": True, "msg": "Atualizado.", "count": count, "alarm": alarm})

        if len(storage) >= MAX_ITEMS:
            return jsonify({"ok": False, "msg": f"Limite de {MAX_ITEMS} atingido."}), 400

        storage.append({"number": number, "name": name})
        save_data()
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
        save_data()
    return jsonify({"ok": True, "msg": "Reset feito."})


@app.route("/all", methods=["GET"])
def get_all():
    with lock:
        return jsonify({"ok": True, "results": storage})


if __name__ == "__main__":
    load_data()  # carrega cadastros já salvos ao iniciar
    app.run(host="0.0.0.0", port=5000, debug=True)

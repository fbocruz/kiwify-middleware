from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/SEU_SCRIPT_ID/exec"

@app.route("/webhook", methods=["POST"])
def receber_webhook():
    try:
        payload = request.json
        print("Webhook recebido da Kiwify:", payload)

        response = requests.post(GOOGLE_SCRIPT_URL, json={"order": payload})
        print("Resposta do Apps Script:", response.text)

        return jsonify({"status": "ok", "retorno_script": response.text}), 200

    except Exception as e:
        print("Erro:", str(e))
        return jsonify({"status": "erro", "mensagem": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

from flask import Flask, request, jsonify
import requests
import gspread
from google.oauth2.service_account import Credentials
import os
import json

app = Flask(__name__)

# 🔗 URL do Apps Script (mantida)
GOOGLE_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxmfWvmh1cKBt02UOBR5Ax_R624PgIlzhuxVh5yLaIWfmZfu3NYrT-RM-dIlKX6J_Mtrw/exec"

# 🔐 Autenticação com Google Sheets via variável de ambiente
scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
credenciais_json = os.getenv("CREDENCIAIS_JSON")
creds_dict = json.loads(credenciais_json)
creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
client = gspread.authorize(creds)

# 🗂 Nome da planilha e aba
NOME_PLANILHA = "clientes_ativos"
ABA = "Página1"

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

@app.route("/verificar_assinante", methods=["POST"])
def verificar_assinante():
    try:
        username = request.json.get("username")
        if not username:
            return jsonify({"erro": "username não informado"}), 400

        sheet = client.open(NOME_PLANILHA).worksheet(ABA)
        dados = sheet.get_all_records()

        for row in dados:
            if row.get("username") == username:
                return jsonify({
                    "assinatura_ativa": row.get("assinatura_ativa", "").upper() == "TRUE",
                    "nome": row.get("nome") or ""
                }), 200

        return jsonify({"assinatura_ativa": False}), 200
    except Exception as e:
        print("Erro na verificação:", str(e))
        return jsonify({"erro": str(e)}), 500

@app.route("/vincular_nome", methods=["POST"])
def vincular_nome():
    try:
        username = request.json.get("username")
        nome = request.json.get("nome")
        email = request.json.get("email")
        print(username)
        print(nome)
        print(email)
        sheet = client.open(NOME_PLANILHA).worksheet(ABA)
        dados = sheet.get_all_values()

        if email:  # 🆕 Tratamento por e-mail
            for i, row in enumerate(dados[1:], start=2):  # começa da linha 2
              if len(row) > 0 and row[0].strip().lower() == email.strip().lower():
                    nome_usuario = row[7] or "Assinante"
                    sheet.update_cell(i, 6, "TRUE")      # assinatura_ativa
                    sheet.update_cell(i, 7, username)    # username
                    sheet.update_cell(i, 8, nome_usuario)  # nome_usuario
                    return jsonify({"vinculado": True, "nome": nome_usuario}), 200
            return jsonify({"vinculado": False}), 404

        if not username or not nome:
            return jsonify({"erro": "username ou nome não informados"}), 400

        # Lógica anterior (por nome)
        for i, row in enumerate(dados[1:], start=2):
            if row[0] == "":
                continue
            if row[0] == username or row[6] == username:
                sheet.update_cell(i, 6, "TRUE")
                sheet.update_cell(i, 7, username)
                sheet.update_cell(i, 8, nome)
                return jsonify({"status": "atualizado"}), 200

        return jsonify({"status": "nao_encontrado"}), 404

    except Exception as e:
        print("Erro no vínculo:", str(e))
        return jsonify({"erro": str(e)}), 500


@app.route("/", methods=["GET"])
def keep_alive():
    return "Online", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

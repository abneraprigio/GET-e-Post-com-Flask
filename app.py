"""Sistema Escola: HTML + API JSON + MySQL, para explicar em sala."""

import os  # Lê a configuração do MySQL no computador, sem gravar senha aqui.
from flask import Flask, jsonify, render_template, request
import mysql.connector  # Biblioteca que conversa com o servidor MySQL.
from mysql.connector import Error, IntegrityError  # Tipos de falha do MySQL.

app = Flask(__name__)  # Cria a aplicação que receberá requisições HTTP.


def conectar():  # Esta função é a ponte entre Python e Banco de Dados.
    return mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', '127.0.0.1'),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', 'senai105'),
        database=os.getenv('MYSQL_DATABASE', 'escola_informatica_aula_dml')
    )


@app.get('/')  # Quando o navegador faz GET na página inicial...
def inicio():
    return render_template('index.html')  # Flask entrega HTML ao navegador.


@app.get('/api/saudacao')  # GET na URL da primeira API.
def saudacao():
    return jsonify({'mensagem': 'API da Escola funcionando!'}), 200


@app.get('/api/alunos')  # GET consulta alunos; não grava nada no banco.
def listar_alunos():
    banco = None   # Inicializar permite fechar apenas se a conexão abriu.
    cursor = None  # Cursor executa comandos SQL dentro da conexão.
    try:
        banco = conectar()  # Python abre a conexão com o MySQL.
        cursor = banco.cursor(dictionary=True)  # Cada linha vira dicionário.
        cursor.execute('SELECT aluno_id, nome, email, telefone '
                       'FROM alunos ORDER BY aluno_id DESC LIMIT 20')
        alunos = cursor.fetchall()  # Lê as linhas retornadas pelo SELECT.
        return jsonify(alunos), 200  # Python entrega JSON ao cliente.
    except Error:  # Um erro de conexão ou consulta não derruba a aplicação.
        app.logger.exception('Erro ao consultar alunos')
        return jsonify({'erro': 'Não foi possível consultar o MySQL.'}), 503
    finally:  # Este bloco roda mesmo quando houve erro ou return.
        if cursor is not None:
            cursor.close()  # Libera o cursor.
        if banco is not None:
            banco.close()  # Encerra a conexão com o banco.


@app.post('/api/alunos')
def cadastrar_aluno():
    dados = request.get_json(silent=True)

    # Confere se o navegador enviou um objeto JSON.
    if not isinstance(dados, dict):
        return jsonify({'erro': 'Envie um JSON válido.'}), 400

    nome = dados.get('nome')
    email = dados.get('email')
    telefone = dados.get('telefone')

    # Valida os campos obrigatórios antes de acessar o banco.
    if not isinstance(nome, str) or not nome.strip():
        return jsonify({'erro': 'Informe o nome.'}), 400

    if not isinstance(email, str) or not email.strip():
        return jsonify({'erro': 'Informe o e-mail.'}), 400

    banco = None
    cursor = None

    try:
        banco = conectar()
        cursor = banco.cursor()

        cursor.execute(
            'INSERT INTO alunos (nome, email, telefone) VALUES (%s, %s, %s)',
            (nome.strip(), email.strip(), telefone or None)
        )

        novo_id = cursor.lastrowid  # Guarda o ID gerado pelo MySQL.
        banco.commit()              # Confirma o cadastro.

        # Devolve ao JavaScript o nome e o MESMO novo_id criado acima.
        return jsonify({
            'aluno_id': novo_id,
            'nome': nome.strip()
        }), 201

    except IntegrityError:
        if banco is not None:
            banco.rollback()
        return jsonify({'erro': 'Este e-mail já está cadastrado.'}), 409

    except Error:
        if banco is not None:
            banco.rollback()
        app.logger.exception('Erro ao cadastrar aluno')
        return jsonify({'erro': 'Erro ao cadastrar no banco.'}), 503

    finally:
        if cursor is not None:
            cursor.close()
        if banco is not None:
            banco.close()


if __name__ == '__main__':  # Inicia só ao executar: python app.py.
    app.run(port=5001, debug=True)  # Servidor local da aula, porta já testada.

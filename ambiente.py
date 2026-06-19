import json
from threading import Lock

arquivo = "ambiente.json"
lock = Lock() # Evita race condition

# Valores padrão do sistema (caso ocorra falha, por exemplo o arquivo ser corrompido)
DEFAULT = {
    "TEMP": 0.0,
    "UMID": 0.0,
    "CO2": 0.0
}

# Usada por ler_ambiente
def carregar_arquivo():
    try:
        with open(arquivo, "r") as f:
            conteudo = f.read().strip()

            if not conteudo:
                return DEFAULT.copy()

            return json.loads(conteudo)

    except (FileNotFoundError, json.JSONDecodeError):
        return DEFAULT.copy()

# Usada pelos sensores
def ler_ambiente():
    with lock:
        return carregar_arquivo()

# Usada pelo simulador
def salvar_ambiente(dados):
    with lock:
        with open(arquivo, "w") as f:
            json.dump(dados, f, indent=4)

# Usada pelos atuadores que incrementam e decrementam as variáveis
def alterar_valor(campo, delta):
    with lock:
        dados = carregar_arquivo()
        dados[campo] = float(dados.get(campo, 0.0)) + float(delta)

        with open(arquivo, "w") as f:
            json.dump(dados, f, indent=4)
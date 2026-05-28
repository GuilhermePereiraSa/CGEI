### protocolo.py
### Descrever comportamentos comuns de todos os agentes dessa rede.


# Client configura LIMITES dos param -> Gerenciador guarda param
## Sensores apenas informam a cada 1 seg sobre o "ambiente"
# Sensor envia dados -> Gerenciador que avalia se
## determinado param tenha sido "violado"/tenha a constraint violada (entre min e max)
## então: Gerenciador envia comando -> Atuador
## Atuador: "AFIRMATIVO! Qual a próxima mensagem" (ACK) -> Gerenciador

## Sensor notifica -> Gerenciador, sendo valor único retornado ao cliente
## quando pedir certa informação sobre um determinado paramêtro.

header_padrao = [
    "Protocol-Name",
    "Message-Type",
    "Sender-ID",
    "Target-ID",
    "Length",
    "Checksum",
    "Payload",
]
msg_tipos_padroes = [
    "CONNECT",
    "ACK",
    "CONFIG_LIMITS",
    "READ_SENSOR",
    "RESPONSE",
    "COMMAND",
    "DATA",
]
tipos_padroes = ["SENSOR", "ATUADOR", "CLIENTE", "GERENCIADOR"]
payload_padroes = ["OK", "Conectado", "SUCCESS", "TURN_ON", "TURN_OFF"]


class Dispositivo:
    def __init__(self, id_completo: str):
        self.id_str = id_completo
        # ATUADOR_AQUEC_03
        parserId = id_completo.split("_")

        if len(parserId) > 3 or len(parserId) < 1:
            raise ValueError(
                f"ERROR: ID inválido. {id_completo} deve seguir COMPONENTE_FUNCAO_XX ou COMPONENTE ou COMPONENTE_XX"
            )

        self.tipo = parserId[0]

        self.funcao = parserId[1] if len(parserId) >= 2 else None

        self.num = parserId[2] if len(parserId) == 3 else None

        self.validar_tipo(self.tipo)

    def __str__(self) -> str:
        return f"Dispositivo: {self.tipo}\nFuncionalidade: {self.funcao}\nNúmero Sequência: {self.num}"

    def validar_tipo(self, tipo: str):
        if tipo not in tipos_padroes:
            raise ValueError("ERROR: Tipo de componente desconhecido")

    def calcular_checksum(self, payload: str) -> int:
        # Soma os valores ASCII dos chars do payload
        return sum(ord(c) for c in payload)

    # colocado um valor default para payload
    def criar_mensagem(self, msg_type: str, target_id: str, payload: str = "") -> bytes:
        # Criar uma mensagem padrao para o CGEI a ser enviada por socket

        length = len(payload)
        # se menor que TANTO deve ter um padding?

        checksum = self.calcular_checksum(payload)

        mensagem = (
            f"Protocol-Name: CGEI\r\n"
            f"Message-Type: {msg_type}\r\n"
            f"Sender-ID: {self.id_str}\r\n"
            f"Target-ID: {target_id}\r\n"
            f"Length: {length}\r\n"
            f"Checksum: {checksum}\r\n"
            f"Payload: {payload}"
        )

        return mensagem.encode("utf-8")

    def abrir_mensagem(self, msg: bytes) -> dict[str, str]:
        str_completa = msg.decode("utf-8")

        partes = str_completa.splitlines()

        header_dict = {}
        for linha in partes:
            chave, valor = linha.split(":", 1)

            header_dict[chave.strip()] = valor.strip()

        return header_dict

    def tamanho_payload(self, payload: str) -> int:
        return len(payload.encode("utf-8"))

    def verificar_payload(self, payload: str):  # -> bool:
        # se nao esta com identificador unico dos atuadores
        # se nao esta com identificador unico dos sensores
        # se nao tem temperatura min max
        # se nao é um float

        pass

    def validar_msg(self, dict_header: dict[str, str]) -> bool:
        # checar erros no header
        for i, key in enumerate(dict_header.keys()):
            # i, key_1: value_1
            if header_padrao[i] != key:
                raise ValueError("Erro no header")

        if dict_header["Protocol-Name"] != "CGEI":
            raise ValueError("ERROR: envio de mensagem para protocolo desconhecido")

        if dict_header["Message-Type"] not in msg_tipos_padroes:
            raise ValueError("ERROR: tipo da mensagem desconhecido")

        if dict_header["Sender-ID"] not in tipos_padroes:
            raise ValueError("ERROR: tipo de componente do remetente desconhecido")

        # checa conteudo do target-id
        target_id = dict_header["Target-ID"]
        self.validar_tipo(target_id)

        if dict_header["Length"] != self.tamanho_payload(dict_header["Payload"]):
            raise ValueError(
                "ERROR: valor do LENGTH não condiz com tamanho do payload\n"
            )

        # checar conteudo checksum
        payload_atual = dict_header["Payload"]
        checksum_atual = dict_header["Checksum"]

        if self.calcular_checksum(payload_atual) != checksum_atual:
            print("Checksum incorreto. Erro na mensagem")

        ## checar payload - completar verificar_payload
        ## e utilizar o payload_padroes

        return True

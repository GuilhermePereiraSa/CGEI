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


class Dispositivo:
    def __init__(self, id_completo: str):
        self.id_str = id_completo
        # ATUADOR_AQUEC_03
        parserId = id_completo.split("_")

        if len(parserId) > 3 or len(parserId) < 1:
            raise ValueError(
                f"ID inválido. {id_completo} deve seguir COMPONENTE_FUNCAO_XX ou COMPONENTE ou COMPONENTE_XX"
            )

        self.tipo = parserId[0]

        self.funcao = parserId[1] if len(parserId) >= 2 else None

        self.num = parserId[2] if len(parserId) == 3 else None

        if self.tipo not in ["SENSOR", "ATUADOR", "CLIENTE", "GERENCIADOR"]:
            raise ValueError("Tipo de componente desconhecido")

    def __str__(self) -> str:
        return f"Dispositivo: {self.tipo}\nFuncionalidade: {self.funcao}\nNúmero Sequência: {self.num}"

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

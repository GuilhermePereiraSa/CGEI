'''
    A classe Dispositivo é utilizada como base para todos os componentes 
    do sistema, sendo responsável pela criação, validação e interpretação 
    de mensagens, além da implementação do three-way handshake utilizado no 
    estabelecimento das conexões.

    As mensagens seguem um formato padronizado contendo cabeçalho, 
    identificadores de origem e destino, tipo da mensagem, tamanho, checksum 
    e payload. Antes de serem processadas, todas as mensagens passam por 
    verificações de integridade e consistência, garantindo que estejam de 
    acordo com as regras definidas pelo protocolo.
'''

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
  
        parserId = id_completo.split("_")

        if len(parserId) > 3 or len(parserId) < 1:
            raise ValueError(
                f"ERROR: ID inválido. {id_completo} deve seguir COMPONENTE_FUNCAO_XX ou COMPONENTE ou COMPONENTE_XX"
            )

        # tipo dispositivo
        self.tipo = parserId[0]

        # qual é a funcionalidade daquele dispositivo, cada dispositivo tem 1 funcionalidade
        self.funcao = parserId[1] if len(parserId) >= 2 else None

        # número para identificação unica
        self.num = parserId[2] if len(parserId) == 3 else None

        self.validar_tipo(self.tipo)

    def __str__(self) -> str:
        return f"Dispositivo: {self.tipo}\nFuncionalidade: {self.funcao}\nNúmero Sequência: {self.num}"

    def validar_tipo(self, tipo: str):
        if tipo not in tipos_padroes:
            raise ValueError(f"ERROR: Tipo de componente desconhecido ({tipo})")

    def calcular_checksum(self, payload: str) -> int:
        # Soma os valores ASCII dos chars do payload
        return sum(ord(c) for c in payload)

    # colocado um valor default para payload
    def criar_mensagem(self, tipo: str, target_id: str, payload: str = "") -> bytes:
        # Criar uma mensagem padrao para o CGEI a ser enviada por socket

        length = len(payload)

        checksum = self.calcular_checksum(payload)

        mensagem = (
            f"Protocol-Name: CGEI\r\n"
            f"Message-Type: {tipo}\r\n"
            f"Sender-ID: {self.id_str}\r\n"
            f"Target-ID: {target_id}\r\n"
            f"Length: {length}\r\n"
            f"Checksum: {checksum}\r\n"
            f"Payload: {payload}"
        )

        return mensagem.encode("utf-8")

    def abrir_mensagem(self, msg: bytes) -> dict[str, str]:
        str_completa = msg.decode("utf-8")

        # divide str completa
        partes = str_completa.splitlines()

        header_dict = {}
        for linha in partes:
            chave, valor = linha.split(":", 1)
            # funcao de strip para tirar espaços caso tenha
            header_dict[chave.strip()] = valor.strip()

        return header_dict

    def tamanho_payload(self, payload: str) -> int:
        return len(payload.encode("utf-8"))

    def verificar_payload(self, tipo, payload: str):  # -> bool:
        # se nao esta com identificador unico dos atuadores
        # se nao esta com identificador unico dos sensores
        # se nao tem temperatura min max
        # se nao é um float

        if tipo == "CONNECT":
            # Divide pelos "_" conforme especificação do dispositivo
            partes = payload.split("_")
            tipo = partes[0]
            self.validar_tipo(tipo)

        elif tipo == "ACK":
            # Verifica se há mensagem indicando sucesso
            if len(payload.strip()) == 0:
                raise ValueError("ERROR: ACK sem descrição")

        elif tipo == "ERROR":
            # Verifica se há mensagem indicando falha
            if len(payload.strip()) == 0:
                raise ValueError("ERROR: ERROR sem descrição")

        elif tipo == "COMMAND":
            if payload not in payload_padroes:
                raise ValueError("ERROR: comando inválido")

        elif tipo == "DATA":
            try:
                float(payload)
            except ValueError:
                raise ValueError("ERROR: DATA deve conter valor numérico")

        elif tipo == "READ_SENSOR":
            partes = payload.split("_")
            if partes[0] != "SENSOR":
                raise ValueError("ERROR: READ_SENSOR deve conter ID de sensor")

        elif tipo == "RESPONSE":
            try:
                float(payload)
            except ValueError:
                raise ValueError("ERROR: RESPONSE inválido")

        elif tipo == "CONFIG_LIMITS":
            try:
                variavel, minimo, maximo = payload.split(",")
                variaveis_validas = ["TEMP", "UMID", "CO2"]

                if variavel not in variaveis_validas:
                    raise ValueError

                minimo = float(minimo)
                maximo = float(maximo)

                if minimo >= maximo:
                    raise ValueError("ERROR: mínimo deve ser menor que máximo")
            except ValueError:
                raise ValueError("ERROR: CONFIG_LIMITS inválido")
        return True

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

        # checa conteudo do sender-id
        sender_id = dict_header["Sender-ID"]
        tipo_sender = sender_id.split("_")[0]
        self.validar_tipo(tipo_sender)

        # checa conteudo do target-id
        target_id = dict_header["Target-ID"]
        tipo_target = target_id.split("_")[0]
        self.validar_tipo(tipo_target)

        if int(dict_header["Length"]) != self.tamanho_payload(dict_header["Payload"]):
            raise ValueError(
                "ERROR: valor do LENGTH não condiz com tamanho do payload\n"
            )

        # checar conteudo checksum
        payload_atual = dict_header["Payload"]
        checksum_atual = int(dict_header["Checksum"])

        if self.calcular_checksum(payload_atual) != checksum_atual:
            print(f"\n[{self.id_str}] Checksum incorreto. Erro na mensagem")

        try:
            self.verificar_payload(dict_header["Message-Type"], dict_header["Payload"])

        except ValueError as e:
            print(f"\n[{self.id_str}] {e}")
            return False

        return True

    def threeway_handshake(self, sock) -> bool:
        try:
            # cliente inicia mandando mensagem para o server
            msg_conn = self.criar_mensagem(
                "CONNECT", "GERENCIADOR", payload=self.id_str
            )
            sock.sendall(msg_conn)

            # caso exceda o tempo tem o timeout
            resposta_ack = sock.recv(1024)

            resposta_dict = self.abrir_mensagem(resposta_ack)

            self.validar_msg(resposta_dict)
            print(
                f"\n[{self.id_str}] Gerenciador respondeu com: {resposta_dict.get('Payload')}"
            )

            ## ERROR
            if resposta_dict["Payload"] == "ERROR":
                raise ValueError(
                    "ERROR: tentativa de conexão com o gerenciador falhou."
                )
            if (
                resposta_dict["Payload"]
                == "GERENCIADOR"  # Alterado (antes era conectado)
                and resposta_dict["Message-Type"] == "CONNECT"  # ACK ou CONNECT?
            ):
                msg_ack = self.criar_mensagem("ACK", "GERENCIADOR", "OK")
                sock.sendall(msg_ack)

                print(f"\n[{self.id_str}] Handshake estabelecido com sucesso!\n")
                return True
            return False

        except Exception as e:
            print(f"\n[{self.id_str}] Erro na comunicação: {e}")
            return False

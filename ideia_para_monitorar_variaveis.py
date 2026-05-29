
class Gerenciador(Dispositivo):
    def __init__(self, id_completo: str):
        super().__init__(id_completo)

        # Gerenciador se comunica com todos os dispositivos
        # sockets dos dispositivos conectados
        self.atuadores = {}
        self.sensores = {}
        self.cliente = None

        # Estado dos atuadores e histerese
        self.histerese = 2.0

        # False -> desligado, True -> ligado
        self.estado_atuadores = {
            "ATUADOR_AQUEC_1": False,
            "ATUADOR_RESF_1": False,
            "ATUADOR_IRRIG_1": False,
            "ATUADOR_CO2_1": False
        }

        # limites configuráveis
        self.temperaturaMax = 30.0
        self.temperaturaMin = 20.0

        self.co2Max = 1000.0
        self.co2Min = 300.0

        self.umidadeMax = 70.0
        self.umidadeMin = 40.0

    def criar_mensagem(self, msg_type: str, target_id: str, payload: str = "") -> bytes:
        return super().criar_mensagem(msg_type, target_id, payload)

    def __repr__(self) -> str:
        return super().__repr__()

    def iniciar_escuta(self, host="0.0.0.0", port=5000):

        # thread monitoramento das variáveis do ambiente
        thread_monitor = Thread(
            target=self.monitorar_variaveis,
            daemon=True
        )

        thread_monitor.start()

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # reuse mesmo address caso reabra
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.server_socket.bind((host, port))

        self.server_socket.listen(5)  # 5 queue espera de conexões

        print(f"Gerenciador escutando em {host}:{port}")

        try:
            while True:

                conn, addr = self.server_socket.accept()

                print(f"Nova conexão de {addr}")

                thread_conn = Thread(
                    target=self.tratar_conexao,
                    args=(conn, addr),
                    daemon=True
                )

                thread_conn.start()

        except KeyboardInterrupt:
            print("Gerenciador encerrando atividades...")

        except OSError as e:
            if e.errno == errno.EADDRINUSE:
                print("Port already in use")

    def tratar_conexao(self, conn, addr):
        try:
            while True:

                dados = conn.recv(1024)

                if not dados:
                    print(f"{addr} desconectado")
                    break

                msg_dict = self.abrir_mensagem(dados)

                self.validar_msg(msg_dict)

                sender = msg_dict["Sender-ID"]
                tipo_msg = msg_dict["Message-Type"]
                payload = msg_dict["Payload"]

                print(f"\n[{sender}] -> {tipo_msg} | {payload}")

                # Registro do dispositivo
                if tipo_msg == "CONNECT":

                    if "ATUADOR" in sender:
                        self.atuadores[sender] = conn
                        print(f"{sender} registrado como atuador")

                    elif "SENSOR" in sender:
                        self.sensores[sender] = conn
                        print(f"{sender} registrado como sensor")

                    elif "CLIENTE" in sender:
                        self.cliente = conn
                        print(f"{sender} registrado como cliente")

                    resposta = self.criar_mensagem(
                        "CONNECT",
                        sender,
                        "Conectado"
                    )

                    conn.sendall(resposta)

                # Valores enviados pelos sensores
                elif tipo_msg == "DATA":

                    valor = float(payload)

                    if "TEMP" in sender:
                        ambiente.TEMPERATURA = valor

                    elif "UMID" in sender:
                        ambiente.UMIDADE = valor

                    elif "CO2" in sender:
                        ambiente.CO2 = valor

                # ACK dos atuadores
                elif tipo_msg == "ACK":
                    print(f"ACK recebido: {payload}")

        except Exception as e:
            print(f"Erro de conexão: {e}")

        finally:
            conn.close()

    def enviar_comando(self, atuador_id, comando):

        conn = self.atuadores.get(atuador_id)

        if not conn:
            print(f"{atuador_id} não conectado")
            return

        msg = self.criar_mensagem(
            "COMMAND",
            atuador_id,
            comando
        )

        conn.sendall(msg)

        self.estado_atuadores[atuador_id] = (
            comando == "TURN_ON"  # Muda o estado para true ou false
        )

        print(f"Gerenciador enviou {comando} para {atuador_id}")

    # Executada pela thread inicializada em iniciar_escuta
    def monitorar_variaveis(self):

        while True:

            controles = [
                {
                    "valor": ambiente.TEMPERATURA,
                    "min": self.temperaturaMin,
                    "max": self.temperaturaMax,
                    "atuador_min": "ATUADOR_AQUEC_1",
                    "atuador_max": "ATUADOR_RESF_1"
                },

                {
                    "valor": ambiente.UMIDADE,
                    "min": self.umidadeMin,
                    "max": self.umidadeMax,
                    "atuador_min": "ATUADOR_IRRIG_1",
                    "atuador_max": None
                },

                {
                    "valor": ambiente.CO2,
                    "min": self.co2Min,
                    "max": self.co2Max,
                    "atuador_min": "ATUADOR_CO2_1",
                    "atuador_max": None
                }
            ]

            for controle in controles:

                valor = controle["valor"]
                minimo = controle["min"]
                maximo = controle["max"]

                atuador_min = controle["atuador_min"]
                atuador_max = controle["atuador_max"]

                # Controle de limite máximo
                if atuador_max:

                    # liga
                    if valor > maximo and not self.estado_atuadores[atuador_max]:
                        self.enviar_comando(atuador_max, "TURN_ON")

                    # desliga com histerese
                    elif valor < maximo - self.histerese and self.estado_atuadores[atuador_max]:
                        self.enviar_comando(atuador_max, "TURN_OFF")

                # Controle de limite mínimo
                if atuador_min:

                    # liga
                    if valor < minimo and not self.estado_atuadores[atuador_min]:
                        self.enviar_comando(atuador_min, "TURN_ON")

                    # desliga com histerese
                    elif valor > minimo + self.histerese and self.estado_atuadores[atuador_min]:
                        self.enviar_comando(atuador_min, "TURN_OFF")

            print(
                f"[AMBIENTE] "
                f"TEMP={ambiente.TEMPERATURA:.2f} | "
                f"UMID={ambiente.UMIDADE:.2f} | "
                f"CO2={ambiente.CO2:.2f}"
            )

            time.sleep(1)

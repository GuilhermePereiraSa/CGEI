'''
    Após iniciar a escuta por conexões, o gerenciador passa a executar duas threads. 
    Uma delas é responsável por tratar as conexões estabelecidas pelos demais dispositivos, 
    enquanto a outra realiza o monitoramento contínuo do ambiente. Essa divisão permite que o 
    sistema acompanhe as condições do ambiente e acione os atuadores necessários para manter 
    as variáveis dentro dos limites estabelecidos, de forma simultânea.

    O gerenciador mantém os valores da última leitura realizada pelos sensores em
    variáveis locais, tendo em vista que ele não acessa diretamente o arquivo ambiente.json
    que contém os valores atuais da variáveis, o que fica a cargo dos sensores, que a cada 1s, 
    enviam suas leituras ao gerenciador.
'''

import errno
import socket
import time
from threading import Thread

# from threading import Thread
from protocolo import Dispositivo


class Gerenciador(Dispositivo):
    def __init__(self, id_completo: str):
        super().__init__(id_completo)

        # O gerenciador só guarda o valor da última leitura enviada pelos sensores,
        # ele não lê o arquivo diretamente
        self.ambiente_local = {"TEMP": 0.0, "UMID": 0.0, "CO2": 0.0}

        # min e max default, esses valores podem ser alterados pelo Cliente
        self.temperaturas = [18.0, 26.0]
        self.umidades = [40.0, 70.0]
        self.co2 = [300.0, 800.0]

        # sockets dos dispositivos conectados
        # 1_gerenciador-> n_atuadores, n_sensores, n_clientes
        self.atuadores = {}  
        self.sensores = {}
        self.cliente = {}

        # Estado dos atuadores e histerese
        self.histerese = 2.0

        # False -> desligado, True -> ligado
        self.estado_atuadores = {
            "ATUADOR_AQUEC_1": False,
            "ATUADOR_RESF_1": False,
            "ATUADOR_IRRIG_1": False,
            "ATUADOR_CO2_1": False,
        }

    def criar_mensagem(self, tipo: str, target_id: str, payload: str = "") -> bytes:
        return super().criar_mensagem(tipo, target_id, payload)

    def __repr__(self) -> str:
        return super().__repr__()

    def iniciar_escuta(self, host="0.0.0.0", port=5000):
        # Criação e inicialização da thread de monitoramento das variáveis
        Thread(target=self.monitorar_variaveis, daemon=True).start()
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # reúsa mesmo address caso reabra
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((host, port))
        self.server_socket.listen(5)  # fila de espera de conexões (limite de 5)

        print(f"Gerenciador escutando em {host}:{port}")

        try:
            while True:
                conn, addr = self.server_socket.accept()
                print(f"Connected by {conn}")
                # Criação e inicialização da thread de tratamento de conexões
                Thread(
                    target=self.tratar_conexao, args=(conn, addr), daemon=True
                ).start()

        except KeyboardInterrupt:
            print("Gerenciador encerrando atividades...")
        except OSError as e:
            if e.errno == errno.EADDRINUSE:
                print("Port already in use")

    def enviar_comando(self, atuador_id, comando: str):
        conn = self.atuadores.get(atuador_id)

        if not conn:
            return

        msg = self.criar_mensagem("COMMAND", atuador_id, comando)

        conn.sendall(msg)

        self.estado_atuadores[atuador_id] = (
            comando == "TURN_ON"  # Muda o estado para true ou false
        )
        print(f"Gerenciador enviou {comando} para {atuador_id}")
    
    # Thread de tratamento de conexões
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

                    # Essa msg não contém mais o payload "Conectado",
                    # para ser possível validação correta do payload das outras msgs do tipo CONNECT,
                    # o que difere do especificado no relatório anterior.
                    resposta = self.criar_mensagem("CONNECT", sender, "GERENCIADOR")
                    conn.sendall(resposta)

                # Valores enviados pelos sensores
                elif tipo_msg == "DATA":
                    valor = float(payload)
                    campo = ""

                    if "TEMP" in sender:
                        campo = "TEMP"
                    elif "UMID" in sender:
                        campo = "UMID"
                    elif "CO2" in sender:
                        campo = "CO2"

                    # Salva a última leitura no ambiente local para o gerenciador 
                    # tomar decisões na função monitorar_variaveis ou responder a
                    # mensagens do tipo READ_SENSOR enviadas pelo Cliente
                    self.ambiente_local[campo] = valor

                elif tipo_msg == "ACK":
                    print(f"ACK recebido: {payload}")

                elif tipo_msg == "READ_SENSOR":
                    sensor_id = payload
                    if "TEMP" in sensor_id:
                        valor = self.ambiente_local["TEMP"]
                    elif "UMID" in sensor_id:
                        valor = self.ambiente_local["UMID"]
                    elif "CO2" in sensor_id:
                        valor = self.ambiente_local["CO2"]
                    else:
                        valor = -1.0

                    resposta = self.criar_mensagem("RESPONSE", sender, str(valor))
                    conn.sendall(resposta)

                elif tipo_msg == "CONFIG_LIMITS":
                    # VAR,min,max
                    partes = payload.split(",")
                    if len(partes) == 3:
                        var = partes[0]
                        minimo = float(partes[1])
                        maximo = float(partes[2])
                        
                        if var == "TEMP":
                            self.temperaturas = [minimo, maximo]
                        elif var == "UMID":
                            self.umidades = [minimo, maximo]
                        elif var == "CO2":
                            self.co2 = [minimo, maximo]

                        ack = self.criar_mensagem(
                            "ACK", sender, "Limites atualizados com sucesso."
                        )
                        conn.sendall(ack)

        except Exception as e:
            print(f"Erro de conexão: {e}")

        finally:
            conn.close()

    # Thread de monitoramento das variáveis do ambiente
    def monitorar_variaveis(self):
        while True:
            controles = [
                {
                    "valor": self.ambiente_local["TEMP"],
                    "min": self.temperaturas[0],
                    "max": self.temperaturas[1],
                    "atuador_min": "ATUADOR_AQUEC_1",
                    "atuador_max": "ATUADOR_RESF_1",
                },
                {
                    "valor": self.ambiente_local["UMID"],
                    "min": self.umidades[0],
                    "max": self.umidades[1],
                    "atuador_min": "ATUADOR_IRRIG_1",
                    "atuador_max": None,
                },
                {
                    "valor": self.ambiente_local["CO2"],
                    "min": self.co2[0],
                    "max": self.co2[1],
                    "atuador_min": "ATUADOR_CO2_1",
                    "atuador_max": None,
                },
            ]

            for controle in controles:
                valor = controle["valor"]

                # EVITA ACIONAMENTO FANTASMA
                # antes dos sensores conectarem,
                # depois fica normal, é so para
                # evitar esses TURN ON -> TURN OFF no inicio
                if valor is None:
                    continue
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
                    elif (
                        valor < maximo - self.histerese
                        and self.estado_atuadores[atuador_max]
                    ):
                        self.enviar_comando(atuador_max, "TURN_OFF")

                # Controle de limite mínimo
                if atuador_min:
                    # liga
                    if valor < minimo and not self.estado_atuadores[atuador_min]:
                        self.enviar_comando(atuador_min, "TURN_ON")

                    # desliga com histerese
                    elif (
                        valor > minimo + self.histerese
                        and self.estado_atuadores[atuador_min]
                    ):
                        self.enviar_comando(atuador_min, "TURN_OFF")

            # fim for
            temp_str = (
                f"{self.ambiente_local['TEMP']:.2f}"
                if self.ambiente_local["TEMP"] is not None
                else "AGUARDANDO"
            )
            umid_str = (
                f"{self.ambiente_local['UMID']:.2f}"
                if self.ambiente_local["UMID"] is not None
                else "AGUARDANDO"
            )
            co2_str = (
                f"{self.ambiente_local['CO2']:.2f}"
                if self.ambiente_local["CO2"] is not None
                else "AGUARDANDO"
            )

            print(
                f"[GERENCIADOR] "
                f"ambiente -> "
                f"TEMPERATURA={temp_str} | "
                f"UMIDADE={umid_str} | "
                f"CO2={co2_str}"
            )

            # cada 1 segundo
            time.sleep(1)


if __name__ == "__main__":
    gerenciador = Gerenciador("GERENCIADOR")
    gerenciador.iniciar_escuta()

"""
    Foram inicializadas três threads de sensores, sendo uma para cada variável 
    monitorada pelo sistema: temperatura, umidade e concentração de CO2.

    Os sensores realizam leituras diretamente do arquivo ambiente.json, 
    simulando dispositivos que coletam informações do ambiente real. A cada 
    segundo, essas leituras são enviadas ao gerenciador por meio da rede.

    O gerenciador não acessa diretamente o arquivo do ambiente, mantendo 
    apenas os valores mais recentes recebidos dos sensores.
"""

import socket
import time
from threading import Thread
import ambiente
from protocolo import Dispositivo

class Sensor(Dispositivo):
    def __init__(self, id_completo: str, host: str = "127.0.0.1", port: int = 5000):
        super().__init__(id_completo)
        self.host = host
        self.port = port
        self.rodando = False

    def conectar(self):
        self.cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.cliente_socket.connect((self.host, self.port))
            print(
                f"[{self.id_str}] Conectado ao Gerenciador em {self.host}:{self.port}"
            )

            self.threeway_handshake(self.cliente_socket)

            self.rodando = True

            # Requisito 1.3: Após conectar, enviar leitura a cada 1s
            thread_envio = Thread(target=self.enviar_leituras)
            thread_envio.start()

        except ConnectionRefusedError:
            print(f"[{self.id_str}] Falha ao conectar. O Gerenciador está rodando?")

    def obter_leitura(self):
        dados = ambiente.ler_ambiente()

        if self.funcao == "TEMP":
            return dados["TEMP"]
        elif self.funcao == "UMID":
            return dados["UMID"]
        elif self.funcao == "CO2":
            return dados["CO2"]

    def enviar_leituras(self):
        try:
            while self.rodando:
                try:
                    dado = self.obter_leitura()
                    msg_dados = self.criar_mensagem(
                        tipo="DATA", target_id="GERENCIADOR", payload=str(dado)
                    )
                    self.cliente_socket.sendall(msg_dados)
                    print(f"[{self.id_str}] Dado enviado: {dado}")
                    time.sleep(1)  # Requisito 1.3: envio a cada 1s

                except (ConnectionResetError, BrokenPipeError):
                    print(f"[{self.id_str}] Conexão com o Gerenciador foi perdida.")
                    self.rodando = False
                except KeyboardInterrupt:
                    print(f"\n[{self.id_str}] Encerrando sensor.")
                    self.rodando = False
                    self.cliente_socket.close()

        except Exception as e:
            print(f"[{self.id_str}] thread morreu: {e}")
            self.rodando = False

    def iniciar_sensor(self):
        self.conectar()

        try:
            while True:
                if self.rodando:
                    time.sleep(1)
                else:
                    print(f"[{self.id_str}] Tentando reconectar em 5 segundos...")
                    time.sleep(5)
                    self.conectar()
        except Exception as e:
            print(f"[{self.id_str}] Erro inesperado na thread do sensor: {e}")

        finally:
            self.rodando = False
            self.cliente_socket.close()


if __name__ == "__main__":
    sensores = [
        Sensor("SENSOR_TEMP_1"),
        Sensor("SENSOR_UMID_1"),
        Sensor("SENSOR_CO2_1"),
    ]

    threads = []

    for sensor in sensores:
        t = Thread(target=sensor.iniciar_sensor)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

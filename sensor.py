import random
import socket
import time
from threading import Thread

from protocolo import Dispositivo

"""
Módulo do Sensor (Cliente TCP)
- Roda como um processo isolado, simulando um sensor da Estufa Inteligente.
- Handshake: Assim que conecta no Gerenciador, manda uma mensagem "HELLO" com seu ID para cumprir a regra de identificação (Requisito 1.2).
- Cria uma thread dedicada que fica gerando valores aleatórios (Temp, Umid ou CO2) baseados no tipo do sensor e envia mensagens "DATA" a cada 1 segundo para o Gerenciador (Requisito 1.3).
- Trata quedas de conexão de forma amigável, interrompendo o envio caso o servidor (Gerenciador) caia ou seja fechado.
"""


class Sensor(Dispositivo):
    def __init__(self, id_completo: str, host: str = "127.0.0.1", port: int = 5000):
        super().__init__(id_completo)
        self.host = host
        self.port = port
        self.cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.rodando = False

    def conectar(self):
        try:
            self.cliente_socket.connect((self.host, self.port))
            print(
                f"[{self.id_str}] Conectado ao Gerenciador em {self.host}:{self.port}"
            )

            # Requisito 1.2: Sensores devem se conectar e se identificar
            msg_identificacao = self.criar_mensagem(
                tipo="CONNECT", target_id="GERENCIADOR", payload="IDENTIFICACAO_SENSOR"
            )
            self.cliente_socket.sendall(msg_identificacao)

            self.rodando = True

            # Requisito 1.3: Após conectar, enviar leitura a cada 1s
            thread_envio = Thread(target=self.enviar_leituras)
            thread_envio.start()

        except ConnectionRefusedError:
            print(f"[{self.id_str}] Falha ao conectar. O Gerenciador está rodando?")

    def gerar_leitura_simulada(self) -> str:
        # Simula dados dependendo da função do sensor
        if self.funcao == "TEMP":
            return str(round(random.uniform(15.0, 35.0), 2))
        elif self.funcao == "UMID":
            return str(round(random.uniform(30.0, 80.0), 2))
        elif self.funcao == "CO2":
            return str(round(random.uniform(300.0, 800.0), 2))
        return "0.0"

    def enviar_leituras(self):
        try:
            while self.rodando:
                dado = self.gerar_leitura_simulada()
                msg_dados = self.criar_mensagem(
                    tipo="DATA", target_id="GERENCIADOR", payload=dado
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
    # Exemplo de inicialização (pode rodar múltiplos em terminais diferentes)
    # IDs no formato: COMPONENTE_FUNCAO_NUMERO
    meu_sensor = Sensor("SENSOR_TEMP_01")
    meu_sensor.conectar()

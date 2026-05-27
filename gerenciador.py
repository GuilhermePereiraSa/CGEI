## gerenciador.py
#
## Ideia é ser um server, um configurador de paramêtros
## dados pelo usuário, administrador, que passa para os atuadores
## como devem atuar.


import socket
import sys
import time
from threading import Thread

from protocolo import Dispositivo


class Gerenciador(Dispositivo):
    def __init__(self, id_completo: str):
        super().__init__(id_completo)
        self.temperaturaMax = self.temperaturaMin = self.co2Max = self.co2Min = (
            self.umidadeMax
        ) = self.umidadeMin = 0

        # Gerenciador se comunica com todos

        # processa proprio para escutar

    def criar_mensagem(self, msg_type: str, target_id: str, payload: str = "") -> bytes:
        return super().criar_mensagem(msg_type, target_id, payload)

    def __repr__(self) -> str:
        return super().__repr__()

    def iniciar_escuta(self, host="0.0.0.0", port=5000):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # reuse mesmo address caso reabra
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.server_socket.bind((host, port))

        self.server_socket.listen(5)  # 5 queue espera de conexões
        print(f"Gerenciador escutando em {host}:{port}")

        try:
            while True:
                conn_cliente, address_cliente = self.server_socket.accept()

                print(f"Nova conexão estabelecida de {address_cliente}")

                # thread para cliente especifico
                # threadCliente = Thread(target=self.tratar_cliente, args=(conn_cliente,))
                # threadCliente.start()

        except KeyboardInterrupt:
            print("\nEncerrando Gerenciador.")
            self.server_socket.close()

    def tratar_cliente(self, conn_cliente):
        try:
            while True:
                dados = conn_cliente.recv(1024)

                if not dados:
                    print("Cliente desconectado")
                    break
                texto = dados.decode("utf-8")

                # parser message
                print(f"Mensagem recebida: {texto}")
        except Exception as e:
            print(f"Erro de conexão em {e}")
        finally:
            conn_cliente.close()

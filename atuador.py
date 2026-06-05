import errno
import socket
import time
from threading import Thread

import ambiente
from protocolo import Dispositivo


class Atuador(Dispositivo):
    def __init__(self, id_completo: str):
        super().__init__(id_completo)

        # Estado atual do atuador
        self.ligado = False

    def iniciar_atuador(self, host="localhost", port=5000):
        # thread responsável pela atuação contínua
        thread_atuacao = Thread(target=self.executar_atuacao, daemon=True)
        thread_atuacao.start()

        while True:
            try:
                # Conectando com o server
                # socket work
                # AF_INET -> indica uso do IPv4
                # SOCK_STREAM -> indica uso do TCP
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                # DEFINICAO TEMPO LIMITE
                self.sock.settimeout(None)

                self.sock.connect((host, port))

                # envia msg de connect
                if self.threeway_handshake(self.sock):
                    # trata os comandos que chegarem do gerenciador
                    self.tratar_comandos()
                else:
                    self.sock.close()
                    time.sleep(2)

                break

            except ConnectionRefusedError:
                print(f"[{self.id_str}] Connection refused: Server not listening")
                time.sleep(2)

            except TimeoutError:
                print(f"[{self.id_str}] Connection timed out. Retrying")
            except OSError as e:
                if e.errno == errno.EADDRINUSE:
                    print(f"[{self.id_str}] Port already in use")

    def tratar_comandos(self):
        while True:
            try:
                msg = self.sock.recv(1024)

                if not msg:
                    break

                msg_dict = self.abrir_mensagem(msg)

                self.validar_msg(msg_dict)

                comando = msg_dict["Payload"]

                print(f"\n[{self.id_str}] recebeu o comando: {comando}")

                if comando == "TURN_ON":
                    self.ligado = True

                elif comando == "TURN_OFF":
                    self.ligado = False

                # ACK para gerenciador
                ack = self.criar_mensagem(
                    "ACK", "GERENCIADOR", f"{self.id_str} executou {comando}"
                )

                self.sock.sendall(ack)

            except ValueError:
                print(
                    f"\n[{self.id_str}]A mensagem enviada pelo Gerenciador possui erros"
                )

            except Exception as e:
                print(f"[{self.id_str}] Erro ao tratar comando: {e}")
                break

    def executar_atuacao(self):
        while True:
            # Atua continuamente enquanto ligado
            if self.ligado:
                campo = None
                delta = 0
                if "AQUEC" in self.id_str:
                    campo = "TEMP"
                    delta = 0.5

                elif "RESF" in self.id_str:
                    campo = "TEMP"
                    delta = -0.5

                elif "IRRIG" in self.id_str:
                    campo = "UMID"
                    delta = 1

                elif "CO2" in self.id_str:
                    campo = "CO2"
                    delta = 10

                if campo is not None:
                    ambiente.alterar_valor(campo, delta)

            time.sleep(1)


if __name__ == "__main__":
    atuadores = [
        Atuador("ATUADOR_AQUEC_1"),
        Atuador("ATUADOR_RESF_1"),
        Atuador("ATUADOR_IRRIG_1"),
        Atuador("ATUADOR_CO2_1"),
    ]

    threads = []

    for atuador in atuadores:
        t = Thread(target=atuador.iniciar_atuador)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

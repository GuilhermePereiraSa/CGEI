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
                self.sock.settimeout(5.0)

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
                print("Connection refused: Server not listening")
                time.sleep(2)

            except TimeoutError:
                print("Connection timed out. Retrying")
            except OSError as e:
                if e.errno == errno.EADDRINUSE:
                    print("Port already in use")

    def tratar_comandos(self):
        while True:
            try:
                msg = self.sock.recv(1024)

                if not msg:
                    break

                msg_dict = self.abrir_mensagem(msg)

                self.validar_msg(msg_dict)

                comando = msg_dict["Payload"]

                print(f"\nAtuador recebeu o comando: {comando}")

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
                print("\nA mensagem enviada pelo Gerenciador possui erros")

            except Exception as e:
                print(f"Erro no atuador: {e}")
                break

    def executar_atuacao(self):
        while True:
            # Atua continuamente enquanto ligado
            if self.ligado:
                if "AQUEC" in self.id_str:
                    ambiente.TEMPERATURA += 0.5

                elif "RESF" in self.id_str:
                    ambiente.TEMPERATURA -= 0.5

                elif "IRRIG" in self.id_str:
                    ambiente.UMIDADE += 1

                elif "CO2" in self.id_str:
                    ambiente.CO2 += 10

                print(
                    f"[{self.id_str}] "
                    f"TEMP={ambiente.TEMPERATURA:.2f} | "
                    f"UMID={ambiente.UMIDADE:.2f} | "
                    f"CO2={ambiente.CO2:.2f}"
                )

            time.sleep(1)

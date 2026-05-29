import errno
import socket
import time
from threading import Thread
from protocolo import Dispositivo


## Cliente
class Client(Dispositivo):
    def __init__(self, id_completo: str):
        super().__init__(id_completo)

    def iniciar_requisicoes(self, host="localhost", port=5000):
        while True:
            try:
                # Conectando com o server
                # socket work
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                # DEFINICAO TEMPO LIMITE
                self.sock.settimeout(5.0)

                self.sock.connect((host, port))

                # envia msg de connect
                self.threeway_handshake()

                # sendall é o send repetitivamente
                self.tratar_gerenciador()

                break

            except ConnectionRefusedError:
                print("Connection refused: Server not listening")
                time.sleep(2)
            except TimeoutError:
                print("Connection timed out. Retrying")
                continue
            except OSError as e:
                if e.errno == errno.EADDRINUSE:
                    print("Port already in use")

    def threeway_handshake(self):
        try:
            msg_conn = self.criar_mensagem(
                "CONNECT", "GERENCIADOR", payload=self.id_str
            )
            self.sock.sendall(msg_conn)

            # caso exceda o tempo tem o timeout
            resposta_ack = self.sock.recv(1024)

            resposta_dict = self.abrir_mensagem(resposta_ack)

            self.validar_msg(resposta_dict)
            print(f"\nGerenciador respondeu com: {resposta_dict.get('Payload')}")

            ## ERROR
            if resposta_dict["Payload"] == "ERROR":
                raise ValueError(
                    "ERROR: tentativa de conexão com o gerenciador falhou."
                )
            if (
                resposta_dict["Payload"] == "Conectado"
                and resposta_dict["Message-Type"] == "CONNECT"  # ACK ou CONNECT?
            ):
                msg_ack = self.criar_mensagem("ACK", "GERENCIADOR", "OK")
                self.sock.sendall(msg_ack)

                print("\n[+] Handshake estabelecido com sucesso!\n")

        except Exception as e:
            print(f"Erro na comunicação: {e}")

    def tratar_gerenciador(self):
        try:
            while True:
                ### SIMPLIFICADO PARA TESTAR
                print("MENU")
                print("1. Requisitar leitura")
                print("2. Configurar temperatura")
                print("3. Configurar umidade")
                print("4. Configurar CO2")
                print("5. Sair ")

                opcao = int(input("Escolha: "))

                if opcao == 1:
                    pass
                elif opcao == 2:
                    pass
                elif opcao == 3:
                    pass
                elif opcao == 4:
                    pass
                elif opcao == 5:
                    break
                else:
                    print("ERROR: Opção inválida")

            # conversa normal?

            # enviada msg de CONNECT
            # espera a CONNECT + ACK

        except Exception as e:
            print(f"Erro na comunicação: {e}")
        finally:
            self.sock.close()


if __name__ == "__main__":
    cliente = Client("CLIENTE_1")

    cliente.iniciar_requisicoes()

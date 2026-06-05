import errno
import socket
import time

from protocolo import Dispositivo


## Cliente
class Client(Dispositivo):
    def __init__(self, id_completo: str):
        super().__init__(id_completo)

    def iniciar_cliente(self, host="localhost", port=5000):
        while True:
            try:
                # Conectando com o server
                # socket work
                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                # DEFINICAO TEMPO LIMITE
                self.sock.settimeout(5.0)

                self.sock.connect((host, port))

                # envia msg de connect
                self.threeway_handshake(self.sock)

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

                opcao = input("Escolha: ")

                if opcao == "1":
                    sensor_id = input("Digite o ID do Sensor: (ex: SENSOR_TEMP_1): ")
                    msg = self.criar_mensagem("READ_SENSOR", "GERENCIADOR", sensor_id)
                    self.sock.sendall(msg)

                    resposta_gen = self.sock.recv(1024)
                    resp_dict = self.abrir_mensagem(resposta_gen)
                    print(
                        f"\n=> Valor atual de {sensor_id}: {resp_dict.get('Payload')}"
                    )
                elif opcao in ["2", "3", "4"]:
                    dict_variaveis = {"2": "TEMP", "3": "UMID", "4": "CO2"}
                    variavel = dict_variaveis[opcao]

                    min = input(f"Digite o límite mínimo para esta {variavel}: ")
                    max = input(f"Digite o límite máximo para esta {variavel}: ")

                    payload = f"{variavel},{min},{max}"
                    msg = self.criar_mensagem("CONFIG_LIMITS", "GERENCIADOR", payload)
                    self.sock.sendall(msg)

                    resposta_gen = self.sock.recv(1024)
                    resp_dict = self.abrir_mensagem(resposta_gen)
                    print(f"\n=> Gerenciador respondeu: {resp_dict.get('Payload')}")

                elif opcao == "5":
                    print("Encerrando cliente...")
                    break
                else:
                    print("ERROR: Opção inválida")

        except Exception as e:
            print(f"Erro na comunicação: {e}")
        finally:
            self.sock.close()


if __name__ == "__main__":
    cliente = Client("CLIENTE_1")

    cliente.iniciar_cliente()

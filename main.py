from threading import Thread
import time

from gerenciador import Gerenciador
from atuador import Atuador
from cliente import Client
from sensor import Sensor

gerenciador = Gerenciador("GERENCIADOR")

# Atuadores
atuadores = [
    Atuador("ATUADOR_AQUEC_1"),
    Atuador("ATUADOR_RESF_1"),
    Atuador("ATUADOR_IRRIG_1"),
    Atuador("ATUADOR_CO2_1"),
]

# Sensores
sensores = [
    Sensor("SENSOR_TEMP_01"),
    Sensor("SENSOR_UMID_01"),
    Sensor("SENSOR_CO2_01"),
]

cliente = Client("CLIENTE_1")

threads = []

# Thread gerenciador
thread_ger = Thread(
    target=gerenciador.iniciar_escuta,
    daemon=True
)

threads.append(thread_ger)

# Threads atuadores
for atuador in atuadores:
    t = Thread(
        target=atuador.iniciar_atuador,
        daemon=True
    )

    threads.append(t)

# Threads sensores
for sensor in sensores:
    t = Thread(
        target=sensor.iniciar_sensor,
        daemon=True
    )

    threads.append(t)

# Thread cliente
thread_cli = Thread(
    target=cliente.iniciar_requisicoes
)

threads.append(thread_cli)


if __name__ == "__main__":
    thread_ger.start()

    # espera servidor subir
    time.sleep(1)

    # inicia as outras threads
    for t in threads[1:]:
        t.start()

    thread_cli.join()
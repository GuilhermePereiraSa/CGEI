import random
import time
import ambiente


class Simulador:
    def __init__(self):
        self.intervalo = 60 # 1 minuto
        self.rodando = True

    def criar_variacoes(self):
        while self.rodando:
            dados = ambiente.ler_ambiente()

            # Variações aleatórias
            dados["TEMP"] += random.uniform(-10, 10)
            dados["UMID"] += random.uniform(-20, 20)
            dados["CO2"] += random.uniform(-80, 80)

            # Definição de limites
            dados["TEMP"] = round(max(0, min(50, dados["TEMP"])), 2)
            dados["UMID"] = round(max(0, min(100, dados["UMID"])), 2)
            dados["CO2"] = round(max(300, min(2000, dados["CO2"])), 2)

            ambiente.salvar_ambiente(dados)

            print(
                f"[VARIAÇÃO ALEATÓRIA] TEMP={dados['TEMP']:.2f} | "
                f"UMID={dados['UMID']:.2f} | CO2={dados['CO2']:.2f}"
            )

            time.sleep(self.intervalo)

if __name__ == "__main__":
    sim = Simulador()
    sim.criar_variacoes()
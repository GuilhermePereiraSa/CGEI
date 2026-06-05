# 🌱 CGEI - Controle e Gerenciamento de Estufa Inteligente

**Disciplina:** SSC0142 - Redes de Computadores  
**Docente:** Profª. Dra. Kalinka Regina Lucas Jaquie Castelo Branco  

O **CGEI** é um protocolo de comunicação na camada de aplicação desenvolvido para operar, monitorar e automatizar o ecossistema de uma Estufa Inteligente. O projeto foi arquitetado para resolver o problema de comunicação entre diferentes processos distribuídos utilizando sockets TCP.

---

## 📖 Sobre o Projeto

Este repositório contém a implementação prática da Etapa 2 do Trabalho Prático da disciplina. Em uma estufa real, sensores e atuadores são dispositivos fisicamente separados do servidor central. Para simular esse comportamento de forma fiel no sistema operacional, a arquitetura foi desenhada para que **cada componente rode em um processo totalmente isolado**, comunicando-se exclusivamente via rede.

Para simular o impacto físico das ações (como um aquecedor elevando a temperatura da sala), os processos utilizam um arquivo compartilhado (`ambiente.json`) gerido através de um sistema de travas (Locks), isolando a física da estufa da lógica de comunicação de redes.

---

## ⚙️ Arquitetura do Sistema

O sistema é composto por 5 frentes principais:

1. **Gerenciador (`gerenciador.py`):** O servidor central. Ele aceita conexões, recebe dados, armazena a última leitura em memória, avalia os limites configuráveis com controle de histerese e despacha comandos.
2. **Sensores (`sensor.py`):** Clientes TCP. Eles se conectam, identificam-se e enviam as leituras das variáveis (Temperatura, Umidade e CO2) a cada 1 segundo.
3. **Atuadores (`atuador.py`):** Clientes TCP. Eles escutam comandos do Gerenciador (`TURN_ON` / `TURN_OFF`), alteram o ambiente físico e respondem com confirmações (`ACK`).
4. **Cliente Externa (`cliente.py`):** Interface para o usuário final (ex: o administrador da estufa) requisitar leituras em tempo real e configurar os limites de atuação do sistema.
5. **Simulador (`simulador_de_variacoes.py`):** Um script auxiliar que introduz o "caos" na estufa, alterando aleatoriamente as variáveis físicas ao longo do tempo para forçar a atuação do sistema.

### O Protocolo (CGEI)
A comunicação ocorre através de um protocolo textual estruturado em chave-valor, inspirado no modelo HTTP. 
Toda mensagem carrega informações de roteamento e integridade, possuindo o seguinte cabeçalho:
* `Protocol-Name`, `Message-Type`, `Sender-ID`, `Target-ID`, `Length`, `Checksum` e `Payload`.

---

## 🚀 Como Executar

Por exigência de design e simulação de redes, os componentes não rodam na mesma Thread. **É necessário abrir múltiplos terminais** para observar o sistema em funcionamento.

### Passo 1: Iniciar o ecossistema e o servidor
Abra um terminal e inicie as variações físicas do ambiente (para gerar os dados):
```bash
python simulador_de_variacoes.py
```

Em um segundo terminal, suba o servidor central:

```bash
python gerenciador.py
```

### Passo 2: Conectar os Atuadores
Abra novos terminais e inicie os atuadores desejados passando seu ID. Eles farão o Three-way handshake e ficarão aguardando comandos:

```bash
python atuador.py ATUADOR_AQUEC_01
python atuador.py ATUADOR_RESF_01

# etc...
```
### Passo 3: Conectar os Sensores
Em outros terminais, conecte os sensores. Eles começarão a disparar a leitura a cada 1 segundo:

```bash
python sensor.py SENSOR_TEMP_01
python sensor.py SENSOR_UMID_01
# etc...
```

### Passo 4: Interação com o Usuário
Por fim, abra um terminal para ser o cliente externo. Um menu interativo será exibido:

```bash
python cliente.py
```
Dica: Através do cliente, configure os limites de Temperatura para uma faixa bem estreita. Você verá instantaneamente o Gerenciador disparar o comando para o Aquecedor ou Resfriador em seus respectivos terminais!

👥 Integrantes do Grupo

* Larissa Pires Moreira Rocha Duarte - 15522358
* Gabriella Almeida - 15528121
* Nicolas Amaral dos Santos - 16304033
* Guilherme Pereira de Sá - 15457161
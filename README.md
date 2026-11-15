# IoT para Monitoramento da Qualidade da Água

Projeto de Trabalho de Conclusão de Curso (TCC) voltado ao desenvolvimento de um sistema de monitoramento da qualidade da água utilizando Internet das Coisas (IoT) e Inteligência Artificial (IA). A solução coleta dados por meio de sensores conectados a um ESP32, transmite as leituras via MQTT, realiza o processamento no backend e disponibiliza os resultados em uma interface gráfica.

O projeto tem como foco o monitoramento ambiental urbano da qualidade da água em rios, lagos e reservatórios, permitindo acompanhar parâmetros físico-químicos e identificar possíveis alterações em suas condições.

## Objetivos do projeto

- Realizar a coleta de dados da água por meio de sensores conectados ao ESP32.
- Transmitir as leituras utilizando comunicação Wi-Fi e o protocolo MQTT.
- Armazenar os dados coletados em um banco de dados PostgreSQL.
- Classificar a qualidade da água por meio de regras e de um modelo de Inteligência Artificial.
- Apresentar as leituras, classificações e histórico em uma interface gráfica.
- Permitir o acompanhamento das condições da água a partir dos dados coletados.

## Arquitetura do sistema

A arquitetura foi desenvolvida de forma integrada, utilizando tecnologias responsáveis pela coleta, transmissão, processamento, armazenamento e visualização dos dados.

```text
┌──────────────────────────────┐
│       Sensores de água       │
│   pH | TDS | Turbidez (NTU)  │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│             ESP32            │
│       Coleta das leituras    │
└──────────────┬───────────────┘
               │ Wi-Fi
               ▼
┌──────────────────────────────┐
│          MQTT                │
│       Broker HiveMQ          │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│           FastAPI            │
│     Recebimento e análise    │
└──────────────┬───────────────┘
               │
        ┌──────┴──────┐
        ▼             ▼
┌──────────────┐ ┌──────────────┐
│ PostgreSQL   │ │ Inteligência │
│    Neon      │ │ Artificial   │
└──────────────┘ └──────────────┘
        │             │
        └──────┬──────┘
               ▼
┌──────────────────────────────┐
│       Interface gráfica      │
│         CustomTkinter        │
└──────────────────────────────┘
```

### Fluxo de funcionamento

1. Os sensores realizam as medições dos parâmetros da água.
2. O ESP32 realiza a leitura dos valores e organiza as informações em formato JSON.
3. Os dados são transmitidos pela rede Wi-Fi utilizando o protocolo MQTT.
4. O backend desenvolvido em FastAPI recebe as mensagens publicadas no broker HiveMQ.
5. As informações são processadas e classificadas conforme os critérios definidos no sistema e pelo modelo de IA.
6. As leituras e os resultados são armazenados no banco de dados PostgreSQL hospedado no Neon.
7. A interface gráfica consulta a API e apresenta os dados em tempo real, as classificações e o histórico de medições.

## Tecnologias utilizadas

| Tecnologia | Aplicação no projeto |
|---|---|
| ESP32 | Microcontrolador responsável pela coleta dos dados |
| C++ / Arduino | Desenvolvimento do firmware do ESP32 |
| Wi-Fi | Comunicação entre o dispositivo e o broker MQTT |
| MQTT | Protocolo de transmissão das leituras |
| HiveMQ | Broker MQTT utilizado na comunicação |
| Python | Desenvolvimento do backend, processamento e IA |
| FastAPI | Criação da API e integração dos componentes |
| PostgreSQL | Banco de dados relacional |
| Neon | Hospedagem do banco de dados PostgreSQL |
| Scikit-learn | Treinamento e utilização do modelo de IA |
| Pandas | Manipulação e preparação dos dados |
| NumPy | Operações e processamento numérico |
| Joblib | Persistência e carregamento do modelo treinado |
| CustomTkinter | Desenvolvimento da interface gráfica |
| Matplotlib | Construção dos gráficos |
| Requests | Comunicação da interface com a API |
| Wokwi | Simulação e testes do ESP32 |

## Parâmetros monitorados

O sistema trabalha com três parâmetros principais:

| Parâmetro | Descrição |
|---|---|
| pH | Indica o nível de acidez ou alcalinidade da água |
| TDS | Representa a concentração de sólidos totais dissolvidos |
| Turbidez (NTU) | Indica a presença de partículas em suspensão na água |

### Conexões dos sensores ao ESP32

| Sensor | GPIO |
|---|---|
| TDS | GPIO 34 |
| pH | GPIO 35 |
| Turbidez | GPIO 32 |

**Atenção:** as conexões analógicas devem respeitar o limite de tensão de entrada do ESP32, que é de até 3,3 V. Os módulos dos sensores podem exigir adequação de tensão antes da conexão ao microcontrolador.

## Comunicação MQTT

A comunicação entre o ESP32 e o backend utiliza o protocolo MQTT, que permite a transmissão de mensagens de maneira leve e eficiente.

**Configurações utilizadas:**

- Broker: `broker.hivemq.com`
- Porta: `1883`
- Protocolo: MQTT
- Tópico: `camila/tcc/agua/leituras`

As leituras são transmitidas em formato JSON, reunindo os valores dos três parâmetros monitorados.

Exemplo de mensagem:

```json
{
  "ph": 7.10,
  "tds": 322.59,
  "turbidez": 2.00
}
```

O backend permanece inscrito no tópico configurado, recebendo as mensagens publicadas pelo ESP32 e encaminhando os dados para processamento e armazenamento.

## Backend e API

O backend foi desenvolvido em Python utilizando o framework FastAPI. Sua responsabilidade é receber as mensagens MQTT, processar as leituras, executar a classificação e realizar a persistência das informações no banco de dados.

Entre suas principais responsabilidades estão:

- Conexão com o broker MQTT.
- Recebimento e interpretação das mensagens JSON.
- Validação dos parâmetros recebidos.
- Classificação da qualidade da água por regras e pelo modelo de IA.
- Armazenamento das leituras no PostgreSQL.
- Disponibilização dos dados para consulta pela interface gráfica.

### Endpoints utilizados pela interface

| Endpoint | Finalidade |
|---|---|
| `/` | Verificação da disponibilidade da API |
| `/api/sensores/status` | Consulta do status e das informações mais recentes dos sensores |
| `/api/sensores/historico` | Consulta do histórico de leituras |

A documentação interativa da API pode ser acessada pelo endereço:

`http://127.0.0.1:8000/docs`

## Banco de dados

O armazenamento utiliza PostgreSQL, com hospedagem na plataforma Neon.

O banco recebe os registros das medições e os resultados de classificação, permitindo consultar o histórico de leituras e disponibilizar informações para a interface gráfica.

Para executar o projeto, é necessário configurar a variável de ambiente `DATABASE_URL` com a string de conexão do banco de dados.

**Importante:** não compartilhe credenciais do banco, senhas de Wi-Fi ou outros dados sensíveis no repositório. Utilize variáveis de ambiente e mantenha os arquivos `.env` fora do Git.

## Inteligência Artificial

O projeto utiliza um modelo de aprendizado de máquina baseado no algoritmo Random Forest, disponibilizado pela biblioteca Scikit-learn.

O modelo foi treinado com dados históricos de qualidade da água provenientes de uma base da CETESB, organizada em planilhas que abrangem o período de 1978 a 2024.

### Preparação dos dados

Durante o processamento da base, foram realizadas etapas de preparação e seleção dos registros, incluindo:

- Leitura das planilhas históricas.
- Tratamento e conversão dos dados.
- Seleção das variáveis utilizadas no treinamento.
- Remoção de registros incompletos para as variáveis consideradas.
- Preparação dos dados para treinamento e avaliação do modelo.

Na etapa documentada, a base apresentava 192.049 registros brutos, dos quais 55.844 amostras completas foram utilizadas no conjunto de dados preparado.

### Classificação

O sistema utiliza três categorias para representar as condições identificadas:

| Classificação | Significado |
|---|---|
| Excelente | Parâmetros dentro dos limites operacionais definidos |
| Atenção | Um ou mais parâmetros apresentam valores que exigem atenção |
| Crítica | Pelo menos um parâmetro ultrapassa os limites críticos definidos |

Os limites operacionais utilizados na classificação são:

| Parâmetro | Excelente | Atenção | Crítica |
|---|---|---|---|
| pH | Entre 6,5 e 8,0 | Abaixo de 6,5 ou acima de 8,0, sem atingir a faixa crítica | Abaixo de 6,0 ou acima de 8,5 |
| Turbidez | Até 5 NTU | Acima de 5 até 15 NTU | Acima de 15 NTU |
| TDS | Abaixo de 500 ppm | De 500 até 1000 ppm | Acima de 1000 ppm |

A classificação geral considera a condição mais restritiva encontrada entre os parâmetros: se algum deles estiver na categoria crítica, o resultado geral será crítico; caso contrário, se algum estiver em atenção, o resultado será atenção.

### Avaliação do modelo

Nos experimentos documentados, o modelo apresentou resultados de acurácia próximos de 99,96% no teste com divisão aleatória dos dados. Também foram realizados experimentos com separação temporal dos registros.

**Limitação importante:** os rótulos utilizados no treinamento foram gerados a partir de regras de classificação baseadas nos próprios parâmetros. Dessa forma, o modelo aprende a reproduzir essas regras. A acurácia elevada demonstra a capacidade de reproduzir a classificação adotada no projeto, mas não comprova, isoladamente, a potabilidade real da água ou a capacidade de prever contaminações futuras.

A probabilidade apresentada pelo modelo representa seu nível de confiança na classificação, não uma garantia de que a água seja própria para consumo.

## Interface gráfica

A aplicação desktop foi desenvolvida utilizando CustomTkinter, com gráficos construídos por meio do Matplotlib.

A interface permite acompanhar as informações recebidas pelo backend e consultar os resultados das análises.

### Dashboard

Apresenta:

- Valores atuais de pH, TDS e turbidez.
- Classificação da qualidade da água baseada nas regras.
- Classificação realizada pela Inteligência Artificial.
- Indicador de confiança do modelo.
- Gráfico de acompanhamento das leituras.

### Histórico

Disponibiliza:

- Consulta das medições armazenadas.
- Visualização dos registros em tabela.
- Pesquisa por data.
- Exportação dos dados em CSV.

### Configurações

Reúne opções relacionadas à configuração da aplicação, como informações de conexão e parâmetros utilizados pela interface.

## Estrutura do projeto

A organização pode variar conforme a versão do repositório. A estrutura abaixo representa a separação dos principais componentes:

```text
TCC/
│
├── backend/
│   ├── main.py
│   ├── water_model.pkl
│   ├── requirements.txt
│   └── ...
│
├── firmware/
│   └── src/
│       └── main.cpp
│
├── frontend.py
│
├── BASE_DADOS_TURBIDEZ_PH_TDS.xlsx
│
├── README.md
│
└── .gitignore
```

O arquivo `water_model.pkl` corresponde ao modelo treinado e utilizado pelo backend. A base de dados em Excel é utilizada na preparação e no treinamento do modelo.

## Como executar o projeto

### 1. Pré-requisitos

Antes de iniciar, é necessário ter instalado:

- Python 3.11.
- Visual Studio Code ou outra IDE de sua preferência.
- Arduino IDE, para trabalhar com o ESP32.
- Driver USB correspondente à placa ESP32, quando necessário.
- Acesso à internet.
- Credenciais de acesso ao banco de dados Neon.

### 2. Clonar o repositório

```bash
git clone URL_DO_REPOSITORIO
```

Entre na pasta do projeto:

```bash
cd NOME_DO_REPOSITORIO
```

### 3. Configurar o ambiente Python

Na raiz do projeto, crie o ambiente virtual:

```bash
py -3.11 -m venv backend/venv
```

Ative o ambiente virtual no Windows PowerShell:

```powershell
.\backend\venv\Scripts\Activate.ps1
```

Instale as dependências do backend:

```bash
pip install fastapi "uvicorn[standard]" paho-mqtt joblib numpy pandas sqlalchemy "psycopg[binary]" scikit-learn openpyxl
```

Instale as dependências da interface:

```bash
pip install customtkinter matplotlib requests
```

### 4. Configurar as variáveis de ambiente

Configure a variável `DATABASE_URL` com a string de conexão do PostgreSQL hospedado no Neon.

Exemplo de configuração:

```env
DATABASE_URL=postgresql+psycopg://USUARIO:SENHA@HOST/BANCO?sslmode=require
```

Utilize as credenciais reais somente no ambiente local. Não publique o arquivo `.env` no GitHub.

### 5. Executar o backend

Abra o terminal na pasta `backend`:

```powershell
cd backend
```

Ative o ambiente virtual, caso ainda não esteja ativo:

```powershell
.\venv\Scripts\Activate.ps1
```

Inicie a API:

```bash
python -m uvicorn main:app --reload
```

A API ficará disponível em:

`http://127.0.0.1:8000`

A documentação pode ser acessada em:

`http://127.0.0.1:8000/docs`

### 6. Executar o frontend

Abra outro terminal na raiz do projeto e ative o ambiente virtual:

```powershell
.\backend\venv\Scripts\Activate.ps1
```

Execute a interface:

```bash
python frontend.py
```

### 7. Executar o firmware ESP32

Para utilizar o dispositivo físico:

1. Abra o Arduino IDE.
2. Instale o suporte à placa ESP32.
3. Instale a biblioteca `PubSubClient`.
4. Abra o código do firmware.
5. Configure o nome e a senha da rede Wi-Fi.
6. Verifique o broker e o tópico MQTT.
7. Selecione a placa e a porta serial correspondente.
8. Conecte os sensores aos pinos definidos no código.
9. Faça o upload do firmware para o ESP32.

O dispositivo deverá conectar-se à rede Wi-Fi e publicar as leituras no tópico MQTT configurado.

**Atenção:** o broker público HiveMQ utilizado no projeto não exige credenciais nessa configuração, mas as mensagens transmitidas em uma porta MQTT sem TLS não devem conter informações sensíveis.

## Testes realizados

Foram realizados testes envolvendo a coleta, transmissão, processamento, classificação e visualização das informações.

### Testes dos sensores

O sensor de pH foi comparado com fitas indicadoras em três condições:

| Amostra | Leitura do sensor | Referência das fitas |
|---|---:|---:|
| Água da torneira | 5,09 | 5,0 |
| Suco de limão | 2,10 | 2,0 |
| Água com bicarbonato | 9,09 | Aproximadamente 9,0 |

Também foram realizados testes de turbidez utilizando amostras de água com diferentes condições, incluindo água bidestilada e amostras preparadas com referências de 20 NTU e 100 NTU.

### Testes de integração

Foram realizados testes de comunicação entre o ESP32, o broker MQTT e o backend, verificando o recebimento das mensagens e o armazenamento dos dados no Neon.

### Testes de classificação

Foram avaliadas três condições de qualidade da água, verificando a correspondência entre a classificação baseada nas regras e a classificação realizada pelo modelo de IA.

| Cenário | pH | Turbidez (NTU) | TDS (ppm) | Resultado |
|---|---:|---:|---:|---|
| 1 | 7,10 | 2,04 | 304,03 | Excelente |
| 2 | 6,17 | 5,00 | 604,15 | Atenção |
| 3 | 5,19 | 5,00 | 985,35 | Crítica |

Os testes demonstraram a integração entre os componentes e a capacidade do sistema de receber, processar, classificar e armazenar as leituras.

## Limitações e trabalhos futuros

Entre as possibilidades de evolução do projeto estão:

- Ampliar a validação dos sensores com equipamentos de referência.
- Realizar novos testes de calibração para os sensores de pH, TDS e turbidez.
- Avaliar o modelo com rótulos independentes das regras utilizadas na classificação.
- Investigar a possibilidade de desenvolver modelos voltados à previsão de alterações na qualidade da água.
- Melhorar a segurança da comunicação entre os dispositivos e o servidor.
- Ampliar a quantidade de parâmetros monitorados.
- Evoluir a interface gráfica e os recursos de visualização.

## Considerações finais

O projeto integra conceitos de Internet das Coisas, comunicação entre dispositivos, desenvolvimento de APIs, banco de dados e Inteligência Artificial em uma solução voltada ao monitoramento da qualidade da água.

A integração entre o ESP32, o MQTT, o backend, o banco de dados e a interface gráfica permite acompanhar as medições e visualizar os resultados das classificações realizadas pelo sistema.

O protótipo representa uma aplicação prática de tecnologias computacionais no monitoramento ambiental, com possibilidades de expansão e aprimoramento em trabalhos futuros.

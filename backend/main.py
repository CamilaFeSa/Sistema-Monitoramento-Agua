import json
import threading
from contextlib import asynccontextmanager
from datetime import datetime
from fastapi import Depends, FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
import joblib
import numpy as np
import paho.mqtt.client as mqtt
import pandas as pd

# --- CONFIGURAÇÃO DO BANCO DE DADOS (POSTGRESQL - NEON CLOUD) ---
from sqlalchemy import JSON, Column, Float, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# URL de conexão segura com o Neon (já inserida corretamente)
SQLALCHEMY_DATABASE_URL =  "postgresql://neondb_owner:npg_QtzM4iy2IKLm@ep-twilight-brook-b4om86n4-pooler.c-6.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class LeituraDB(Base):
    __tablename__ = "leituras"

    id = Column(Integer, primary_key=True, index=True)
    horario = Column(String, index=True)
    ph = Column(Float)
    turbidez_ntu = Column(Float)
    tds_ppm = Column(Float)
    classificacao_regras = Column(String)
    classificacao_ia = Column(String)
    confianca_ia = Column(String)
    status = Column(String)
    detalhes = Column(JSON)


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- CONFIGURAÇÃO MQTT (CONECTADO AO MOSQUITTO LOCAL) ---
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC = "tcc/sensores/agua"

# --- CARREGAMENTO DO MODELO DE IA ---
try:
    ml_model = joblib.load("water_model.pkl")
    print("Modelo de IA (water_model.pkl) carregado com sucesso!")
except Exception as e:
    ml_model = None
    print(f"Aviso: Não foi possível carregar o modelo de IA: {e}")

CLASSES_ML = {
    0: "Excelente / Potável",
    1: "Atenção (Parâmetros limítrofes)",
    2: "Crítica (Fora dos padrões)",
}

ultimo_estado_sensor = {
    "horario": None,
    "ph": 7.0,
    "turbidez_ntu": 0.0,
    "tds_ppm": 0,
    "classificacao_regras": "Aguardando dados...",
    "classificacao_ia": "Aguardando dados...",
    "confianca_ia": "0%",
    "status": "Inativo",
    "detalhes": {},
}


def analisar_qualidade_regras(ph: float, turbidez: float, tds: float):
    detalhes = {}

    if ph < 6.0:
        detalhes["ph"] = "Água muito ácida"
    elif ph > 8.5:
        detalhes["ph"] = "Água muito alcalina/básica"
    else:
        detalhes["ph"] = "pH dentro do ideal"

    if turbidez > 15.0:
        detalhes["turbidez"] = "Turbidez muito alta (água turva/barrenta)"
    elif turbidez > 5.0:
        detalhes["turbidez"] = "Turbidez em estado de alerta"
    else:
        detalhes["turbidez"] = "Turbidez dentro do ideal"

    if tds > 1000.0:
        detalhes["tds"] = "Sólidos dissolvidos muito elevados"
    elif tds > 500.0:
        detalhes["tds"] = "Sólidos dissolvidos em alerta"
    else:
        detalhes["tds"] = "TDS dentro do ideal"

    if (6.5 <= ph <= 8.0) and (turbidez <= 5.0) and (tds < 500):
        classificacao = "Excelente / Potável"
        status_sistema = "Normal"
    elif (6.0 <= ph <= 8.5) and (turbidez <= 15.0) and (tds < 800):
        classificacao = "Atenção (Parâmetros limítrofes)"
        status_sistema = "Alerta"
    else:
        classificacao = "Crítica (Fora dos padrões)"
        status_sistema = "Crítico"

    return classificacao, status_sistema, detalhes


def predizer_qualidade_ml(ph: float, turbidez: float, tds: float):
    if ml_model is None:
        return "Modelo Indisponível", "0%"

    entrada = pd.DataFrame(
        [[ph, turbidez, tds]], columns=["ph", "turbidez", "tds"]
    )
    predicao_classe = ml_model.predict(entrada)[0]
    probabilidades = ml_model.predict_proba(entrada)[0]
    confianca = max(probabilidades) * 100
    rotulo = CLASSES_ML.get(predicao_classe, "Desconhecido")
    return rotulo, f"{confianca:.1f}%"


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("Conectado com sucesso ao Broker MQTT (Mosquitto)!")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Falha na conexão ao MQTT. Código de retorno: {rc}")


def on_message(client, userdata, msg):
    global ultimo_estado_sensor
    try:
        payload = msg.payload.decode("utf-8")
        print(f"\n[MQTT] Nova mensagem recebida no tópico '{msg.topic}': {payload}")
        dados = json.loads(payload)

        ph = float(dados.get("ph", 7.0))
        turbidez = float(dados.get("turbidez", dados.get("turbidez_ntu", 0.0)))
        tds = float(dados.get("tds", dados.get("tds_ppm", 0)))

        class_regras, status_sistema, detalhes = analisar_qualidade_regras(
            ph, turbidez, tds
        )
        class_ia, confianca_ia = predizer_qualidade_ml(ph, turbidez, tds)

        horario_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        leitura_dict = {
            "horario": horario_atual,
            "ph": ph,
            "turbidez_ntu": turbidez,
            "tds_ppm": tds,
            "classificacao_regras": class_regras,
            "classificacao_ia": class_ia,
            "confianca_ia": confianca_ia,
            "status": status_sistema,
            "detalhes": detalhes,
        }

        ultimo_estado_sensor = leitura_dict

        db = SessionLocal()
        try:
            nova_leitura = LeituraDB(**leitura_dict)
            db.add(nova_leitura)
            db.commit()
            print(
                f"[Banco de Dados Neon] Leitura salva: {horario_atual} | IA: {class_ia}"
            )
        except Exception as db_error:
            print(f"[Erro DB] Falha ao salvar no banco: {db_error}")
        finally:
            db.close()

    except Exception as e:
        print(f"Erro ao processar mensagem MQTT: {e}")


def start_mqtt_client():
    try:
        client = mqtt.Client(
            client_id="fastapi_water_backend",
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        )
    except AttributeError:
        client = mqtt.Client(client_id="fastapi_water_backend")

    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
    except Exception as e:
        print(f"Erro ao conectar ao broker MQTT: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    mqtt_thread = threading.Thread(target=start_mqtt_client, daemon=True)
    mqtt_thread.start()
    yield


app = FastAPI(
    title="API Qualidade da Água",
    version="2.0",
    lifespan=lifespan,
    docs_url=None,
)

CUSTOM_CSS = """
<style>
.swagger-ui .wrapper { max-width: 1050px !important; margin: 0 auto !important; padding: 20px !important; }
.swagger-ui .opblock .opblock-summary-path { font-size: 19px !important; font-weight: bold !important; }
.swagger-ui .opblock .opblock-summary-description { font-size: 16px !important; }
.swagger-ui .opblock-section-header h4, .swagger-ui .responses-wrapper .responses-inner h4, .swagger-ui table thead tr th { font-size: 16px !important; }
.swagger-ui .opblock-body pre.microlight, .swagger-ui table td, .swagger-ui button, .swagger-ui .btn { font-size: 15px !important; }
</style>
"""

CUSTOM_JS = """
<script>
function traduzirInterface() {
    const mapa = {
        "Example Value": "Exemplo", "Schema": "Esquema", "Controls Accept header.": "Controla o formato aceito.",
        "Parameters": "Parâmetros", "Try it out": "Testar Rota", "Cancel": "Cancelar", "No parameters": "Sem parâmetros",
        "Responses": "Respostas", "Code": "Código", "Description": "Descrição", "Successful Response": "Resposta com Sucesso",
        "Media type": "Tipo de Mídia", "Execute": "Executar Teste", "Clear": "Limpar", "Download": "Baixar",
        "Curl": "Comando cURL", "Request URL": "URL da Requisição", "Server response": "Resposta do Servidor",
        "Details": "Detalhes", "Response body": "Corpo da Resposta", "Response headers": "Cabeçalhos da Resposta",
        "Links": "Links", "No links": "Sem links"
    };
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, null, false);
    let node;
    while (node = walker.nextNode()) {
        const text = node.nodeValue.trim();
        if (mapa[text]) { node.nodeValue = node.nodeValue.replace(text, mapa[text]); }
    }
}
setInterval(traduzirInterface, 200);
</script>
"""


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    res = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title,
        swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
    )
    html_content = (
        res.body.decode("utf-8")
        .replace("</head>", f"{CUSTOM_CSS}</head>")
        .replace("</body>", f"{CUSTOM_JS}</body>")
    )
    return HTMLResponse(content=html_content)


@app.get(
    "/",
    summary="Status do Servidor",
    response_description="Resposta com Sucesso",
    tags=["Geral"],
)
def read_root():
    return {"status": "Backend FastAPI + Neon PostgreSQL + MQTT ativo!"}


@app.get(
    "/api/sensores/status",
    summary="Status dos Sensores",
    response_description="Resposta com Sucesso",
    tags=["Geral"],
)
def get_sensor_status(db: Session = Depends(get_db)):
    if ultimo_estado_sensor["horario"] is not None:
        return ultimo_estado_sensor

    ultima_leitura = (
        db.query(LeituraDB).order_by(LeituraDB.id.desc()).first()
    )
    if ultima_leitura:
        return {
            "horario": ultima_leitura.horario,
            "ph": ultima_leitura.ph,
            "turbidez_ntu": ultima_leitura.turbidez_ntu,
            "tds_ppm": ultima_leitura.tds_ppm,
            "classificacao_regras": ultima_leitura.classificacao_regras,
            "classificacao_ia": ultima_leitura.classificacao_ia,
            "confianca_ia": ultima_leitura.confianca_ia,
            "status": ultima_leitura.status,
            "detalhes": ultima_leitura.detalhes,
        }

    return ultimo_estado_sensor


@app.get(
    "/api/sensores/historico",
    summary="Histórico das Leituras",
    response_description="Resposta com Sucesso",
    tags=["Geral"],
)
def get_sensor_historico(db: Session = Depends(get_db)):
    leituras_db = (
        db.query(LeituraDB).order_by(LeituraDB.id.desc()).limit(20).all()
    )
    return {"total_leituras": len(leituras_db), "historico": leituras_db}
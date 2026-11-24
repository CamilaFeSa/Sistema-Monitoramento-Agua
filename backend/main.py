from contextlib import asynccontextmanager
from datetime import datetime
import json
import os
import threading

from fastapi import Depends, FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse
import joblib
import numpy as np
import paho.mqtt.client as mqtt
import pandas as pd
from sqlalchemy import JSON, Column, Float, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

# --- CONFIGURAÇÃO DO BANCO DE DADOS (POSTGRESQL - NEON CLOUD) ---
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://neondb_owner:npg_QtzM4iy2IKLm@ep-twilight-brook-b4om86n4-pooler.c-6.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require",
)

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
    classificacao_regras = Column(String, nullable=True, default=None)
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


# --- CONFIGURAÇÃO MQTT ---
MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883

MQTT_TOPICS = [
    "camila/tcc/agua/leituras",
]

# --- MODELO DE INTELIGÊNCIA ARTIFICIAL (RANDOM FOREST) ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "water_model.pkl")

try:
    ml_model = joblib.load(MODEL_PATH)
    print(f"Modelo de IA carregado com sucesso de: {MODEL_PATH}")
except Exception as e:
    ml_model = None
    print(f"Aviso: Não foi possível carregar o modelo de IA ({MODEL_PATH}): {e}")

CLASSES_ML = {
    0: "Dentro da faixa de referência",
    1: "No limite da faixa de referência",
    2: "Fora da faixa de referência",
}

STATUS_POR_CLASSE_IA = {
    "Dentro da faixa de referência": "Dentro da faixa de referência",
    "No limite da faixa de referência": "Dentro da faixa de referência",
    "Fora da faixa de referência": "Fora da faixa de referência",
}


def normalizar_rotulo_faixa(texto: str | None) -> str | None:
    if texto is None:
        return None
    resultado = texto.replace(
        "Limítrofe à faixa de referência", "No limite da faixa de referência"
    ).replace(
        "Limitrofe à faixa de referência", "No limite da faixa de referência"
    )
    resultado = resultado.replace("Limítrofe", "No limite").replace(
        "Limitrofe", "No limite"
    )
    return resultado


def serializar_leitura(leitura: LeituraDB) -> dict:
    return {
        "id": leitura.id,
        "horario": leitura.horario,
        "ph": leitura.ph,
        "turbidez_ntu": leitura.turbidez_ntu,
        "tds_ppm": leitura.tds_ppm,
        "classificacao_regras": normalizar_rotulo_faixa(
            leitura.classificacao_regras
        ),
        "classificacao_ia": normalizar_rotulo_faixa(leitura.classificacao_ia),
        "confianca_ia": leitura.confianca_ia,
        "status": normalizar_rotulo_faixa(leitura.status),
        "detalhes": leitura.detalhes,
    }


ultimo_estado_sensor = {
    "horario": None,
    "ph": 7.0,
    "turbidez_ntu": 0.0,
    "tds_ppm": 0,
    "classificacao_regras": None,
    "classificacao_ia": "Aguardando dados...",
    "confianca_ia": "0%",
    "status": "Inativo",
    "detalhes": {},
}


def gerar_detalhes_sensores(ph: float, turbidez: float, tds: float) -> dict:
    """Apenas resume os valores medidos por sensor sem aplicar regras de decisão."""
    return {
        "ph": f"pH medido: {ph}",
        "turbidez": f"Turbidez medida: {turbidez} NTU",
        "tds": f"TDS medido: {tds} ppm",
    }


def comparar_referencia_normativa(ph: float, turbidez: float, tds: float) -> str:
    """Comparativo de referência para água doce (pH 6.0-9.0, Turbidez <= 100 NTU, TDS <= 500 ppm)."""
    fora = []
    if not (6.0 <= ph <= 9.0):
        fora.append("pH")
    if turbidez > 100.0:
        fora.append("Turbidez")
    if tds > 500.0:
        fora.append("TDS")

    if not fora:
        return "Dentro da faixa de referência"
    return f"Fora da faixa de referência ({', '.join(fora)})"


def predizer_qualidade_ml(ph: float, turbidez: float, tds: float):
    """Avalia a leitura exclusivamente pelo modelo Random Forest treinado."""
    if ml_model is None:
        return "Modelo Indisponível", "Inativo", "0%"

    entrada = pd.DataFrame(
        [[ph, turbidez, tds]],
        columns=["ph", "turbidez", "tds"],
    )
    predicao_classe = ml_model.predict(entrada)[0]
    probabilidades = ml_model.predict_proba(entrada)[0]
    confianca_pct = float(np.max(probabilidades)) * 100.0

    rotulo_bruto = CLASSES_ML.get(predicao_classe, str(predicao_classe))
    rotulo = normalizar_rotulo_faixa(rotulo_bruto) or str(rotulo_bruto)
    status_sistema = STATUS_POR_CLASSE_IA.get(
        rotulo, "Fora da faixa de referência"
    )
    return rotulo, status_sistema, f"{confianca_pct:.1f}%"


def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        print("Conectado com sucesso ao HiveMQ!")
        for topic in MQTT_TOPICS:
            client.subscribe(topic)
            print(f"Inscrito no tópico: {topic}")
    else:
        print(f"Falha na conexão MQTT. Código: {reason_code}")


def on_message(client, userdata, msg):
    global ultimo_estado_sensor

    try:
        payload = msg.payload.decode("utf-8")
        dados = json.loads(payload)

        ph = float(dados["ph"])
        tds = float(dados["tds"])
        turbidez = float(dados["turbidez"])

        if not all(np.isfinite(v) for v in (ph, tds, turbidez)):
            print("[MQTT] Leitura inválida: valor não numérico ou infinito.")
            return

        print(
            f"\n[MQTT] Leitura completa recebida: "
            f"pH={ph}, TDS={tds}, Turbidez={turbidez}"
        )

        class_ia, status_sistema, confianca_ia = predizer_qualidade_ml(
            ph, turbidez, tds
        )
        class_regras = comparar_referencia_normativa(ph, turbidez, tds)
        detalhes = gerar_detalhes_sensores(ph, turbidez, tds)
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
                f"[Banco de Dados Neon] Leitura salva: "
                f"{horario_atual} | Ref: {class_regras} | IA: {class_ia} ({confianca_ia})"
            )
        except Exception as db_error:
            db.rollback()
            print(f"[Erro DB] Falha ao salvar: {db_error}")
        finally:
            db.close()

    except (ValueError, KeyError, json.JSONDecodeError) as e:
        print(f"[MQTT] Mensagem inválida: {e}")
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
        return {
            **ultimo_estado_sensor,
            "classificacao_regras": normalizar_rotulo_faixa(
                ultimo_estado_sensor.get("classificacao_regras")
            ),
            "classificacao_ia": normalizar_rotulo_faixa(
                ultimo_estado_sensor.get("classificacao_ia")
            ),
            "status": normalizar_rotulo_faixa(
                ultimo_estado_sensor.get("status")
            ),
        }

    ultima_leitura = (
        db.query(LeituraDB).order_by(LeituraDB.id.desc()).first()
    )
    if ultima_leitura:
        dado = serializar_leitura(ultima_leitura)
        dado.pop("id", None)
        return dado

    return ultimo_estado_sensor


@app.get(
    "/api/sensores/historico",
    summary="Histórico das Leituras",
    response_description="Resposta com Sucesso",
    tags=["Geral"],
)
def get_sensor_historico(db: Session = Depends(get_db)):
    leituras_db = (
        db.query(LeituraDB).order_by(LeituraDB.id.desc()).limit(100).all()
    )
    historico_normalizado = [serializar_leitura(item) for item in leituras_db]
    return {
        "total_leituras": len(historico_normalizado),
        "historico": historico_normalizado,
    }
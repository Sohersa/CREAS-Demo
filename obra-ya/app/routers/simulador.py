"""
Simulador de chat — permite probar el flujo completo desde el navegador
sin necesitar WhatsApp ni API key de Anthropic.
Usa la BD real para cotizaciones.
"""
import json
from datetime import datetime
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.cotizador import generar_cotizaciones
from app.services.comparador import generar_comparativa_simple, resumir_pedido

router = APIRouter(prefix="/sim", tags=["simulador"])


# Pedidos predefinidos para simular sin Claude
PEDIDOS_DEMO = {
    "concreto": {
        "status": "completo",
        "pedido": {
            "items": [
                {"categoria": "concreto", "producto": "Concreto Premezclado f'c 250", "cantidad": 15, "unidad": "m3",
                 "especificaciones": {"resistencia": "250 kg/cm2", "tipo": "normal"}}
            ],
            "entrega": {"direccion": "Zapopan", "fecha": "2026-04-10", "horario": "7:00-14:00"}
        },
        "mensaje_usuario": "Perfecto, necesitas 15m3 de concreto f'c 250 para Zapopan. Deja cotizo con los proveedores..."
    },
    "acero": {
        "status": "completo",
        "pedido": {
            "items": [
                {"categoria": "acero", "producto": "Varilla Corrugada 3/8", "cantidad": 200, "unidad": "piezas",
                 "especificaciones": {"diametro": "3/8\"", "grado": "42", "longitud": "12m"}},
                {"categoria": "acero", "producto": "Varilla Corrugada 1/2", "cantidad": 50, "unidad": "piezas",
                 "especificaciones": {"diametro": "1/2\"", "grado": "42", "longitud": "12m"}},
            ],
            "entrega": {"direccion": "Tlaquepaque", "fecha": "2026-04-08"}
        },
        "mensaje_usuario": "Listo, 200 varillas del 3/8 y 50 del 1/2 para Tlaquepaque. Cotizando..."
    },
    "mixto": {
        "status": "completo",
        "pedido": {
            "items": [
                {"categoria": "concreto", "producto": "Concreto Premezclado f'c 250", "cantidad": 10, "unidad": "m3"},
                {"categoria": "acero", "producto": "Varilla Corrugada 3/8", "cantidad": 200, "unidad": "piezas"},
                {"categoria": "agregados", "producto": "Grava 3/4", "cantidad": 21, "unidad": "m3"},
                {"categoria": "cementantes", "producto": "Cemento Gris", "cantidad": 100, "unidad": "bultos"},
            ],
            "entrega": {"direccion": "Zapopan", "fecha": "2026-04-10"}
        },
        "mensaje_usuario": "Pedidote! 10m3 concreto, 200 varillas, 21m3 grava y 100 bultos cemento. Cotizando..."
    },
    "block": {
        "status": "completo",
        "pedido": {
            "items": [
                {"categoria": "block", "producto": "Block Concreto 15x20x40", "cantidad": 1000, "unidad": "piezas"},
                {"categoria": "cementantes", "producto": "Cemento Gris", "cantidad": 50, "unidad": "bultos"},
                {"categoria": "cementantes", "producto": "Cal Hidratada", "cantidad": 30, "unidad": "bultos"},
            ],
            "entrega": {"direccion": "Tlajomulco", "fecha": "2026-04-12"}
        },
        "mensaje_usuario": "Un millar de block del 15, 50 bultos de cemento y 30 de cal para Tlajomulco. Cotizando..."
    },
    "impermeabilizante": {
        "status": "completo",
        "pedido": {
            "items": [
                {"categoria": "impermeabilizante", "producto": "Impermeabilizante Acrilico", "cantidad": 5, "unidad": "cubetas"},
                {"categoria": "electrico", "producto": "Cable THW Cal 12", "cantidad": 3, "unidad": "rollos"},
                {"categoria": "tuberia", "producto": "Tubo PVC Sanitario 4", "cantidad": 20, "unidad": "piezas"},
            ],
            "entrega": {"direccion": "Guadalajara", "fecha": "2026-04-09"}
        },
        "mensaje_usuario": "5 cubetas de impermeabilizante, 3 rollos de cable y 20 tubos de drenaje. Cotizando..."
    },
}

# Mensajes que simulan la conversacion del agente (sin Claude API)
RESPUESTAS_AGENTE = {
    "hola": "Que onda! Soy Nico, tu asistente de compras de materiales de construccion. Dime que necesitas para tu obra y te consigo los mejores precios. Puedes pedirme concreto, varilla, grava, cemento, block, y mas!",
    "que vendes": "Manejo los 30 materiales principales de obra:\n\n*CONCRETO:* f'c 150, 200, 250, 300, bombeable\n*ACERO:* Varilla 3/8 a 1\", malla 6x6, alambre, armex\n*AGREGADOS:* Grava, arena, tepetate, piedra braza\n*CEMENTANTES:* Cemento gris, blanco, cal, mortero\n*BLOCK:* Del 15, del 20, tabique rojo\n*TUBERIA:* PVC sanitario 4\", hidraulico 1/2\"\n*OTROS:* Impermeabilizante, cable electrico\n\nDime que ocupas!",
    "default_incompleto": "Para cotizarte necesito algunos datos:\n\n1. Que material exactamente?\n2. Cuantas unidades?\n3. Donde es la entrega? (colonia y municipio)\n4. Para cuando lo necesitas?\n\nCon eso te armo la comparativa en minutos!",
}


class MensajeSimulado(BaseModel):
    mensaje: str
    telefono: str = "5213300000000"


@router.post("/chat")
def simular_chat(msg: MensajeSimulado, db: Session = Depends(get_db)):
    """
    Simula el flujo de chat sin necesitar API de Claude.
    Detecta pedidos por palabras clave y genera cotizaciones reales.
    """
    texto = msg.mensaje.lower().strip()

    # Saludos
    if any(w in texto for w in ["hola", "buenos", "buenas", "hey", "que tal"]):
        return {"respuesta": RESPUESTAS_AGENTE["hola"], "tipo": "saludo"}

    if any(w in texto for w in ["que vendes", "que tienes", "catalogo", "que manejas"]):
        return {"respuesta": RESPUESTAS_AGENTE["que vendes"], "tipo": "catalogo"}

    # Detectar pedido por categoria
    pedido_key = None
    if any(w in texto for w in ["concreto", "olla", "colado", "f'c", "fc "]):
        if any(w in texto for w in ["varilla", "grava", "cemento", "bulto"]):
            pedido_key = "mixto"
        else:
            pedido_key = "concreto"
    elif any(w in texto for w in ["varilla", "malla", "alambre", "armex", "acero"]):
        pedido_key = "acero"
    elif any(w in texto for w in ["block", "tabique", "millar"]):
        pedido_key = "block"
    elif any(w in texto for w in ["impermeabilizante", "cable", "tubo"]):
        pedido_key = "impermeabilizante"

    if pedido_key:
        pedido_data = PEDIDOS_DEMO[pedido_key]
        cotizaciones = generar_cotizaciones(db, pedido_data)
        resumen = resumir_pedido(pedido_data)
        comparativa = generar_comparativa_simple(cotizaciones, resumen)

        return {
            "respuesta": pedido_data["mensaje_usuario"],
            "comparativa": comparativa,
            "cotizaciones_count": len(cotizaciones),
            "tipo": "cotizacion",
        }

    return {"respuesta": RESPUESTAS_AGENTE["default_incompleto"], "tipo": "pregunta"}


@router.get("/", response_class=HTMLResponse)
def pagina_simulador():
    """Chat simulado en el navegador — prueba el flujo completo."""
    return """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nico - Simulador de Chat</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { font-family: 'Inter', system-ui, sans-serif; }
        .chat-bubble { max-width: 85%; white-space: pre-wrap; }
        .chat-container { height: calc(100vh - 220px); }
        @keyframes typing { 0%,80%,100% { opacity: 0; } 40% { opacity: 1; } }
        .dot { animation: typing 1.4s infinite; }
        .dot:nth-child(2) { animation-delay: 0.2s; }
        .dot:nth-child(3) { animation-delay: 0.4s; }
    </style>
</head>
<body class="bg-gray-100 min-h-screen">

    <!-- Header -->
    <div class="bg-green-600 text-white p-4 shadow-lg flex items-center gap-3">
        <div class="w-10 h-10 bg-white rounded-full flex items-center justify-center text-xl font-bold text-green-600">N</div>
        <div>
            <h1 class="font-bold text-lg">Nico</h1>
            <p class="text-xs text-green-200">En linea — Simulador de chat</p>
        </div>
        <a href="/admin/" class="ml-auto text-sm bg-green-700 px-3 py-1 rounded hover:bg-green-800">Panel Admin</a>
    </div>

    <!-- Chat -->
    <div id="chat" class="chat-container overflow-y-auto p-4 space-y-3">
        <!-- Mensaje de bienvenida -->
        <div class="flex justify-start">
            <div class="chat-bubble bg-white rounded-2xl rounded-tl-sm px-4 py-2 shadow text-sm">
                <div class="font-bold text-green-600 text-xs mb-1">Nico</div>
                Que onda! Soy Nico, tu asistente de compras de materiales de construccion.
                <br><br>Prueba escribiendo algo como:
                <br>• "Necesito 15m3 de concreto f'c 250"
                <br>• "Manda 200 varillas del 3/8"
                <br>• "Un millar de block del 15 y 50 bultos de cemento"
                <br>• "5 cubetas de impermeabilizante"
                <br>• "hola" o "que vendes"
                <div class="text-gray-400 text-xs mt-2 text-right">Ahora</div>
            </div>
        </div>
    </div>

    <!-- Botones rapidos -->
    <div class="px-4 py-2 flex flex-wrap gap-2">
        <button onclick="enviar('Necesito 15m3 de concreto f\\'c 250 para Zapopan')" class="bg-orange-100 text-orange-700 px-3 py-1 rounded-full text-xs hover:bg-orange-200">Concreto</button>
        <button onclick="enviar('200 varillas del 3/8 y 50 del medio')" class="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-xs hover:bg-blue-200">Varilla</button>
        <button onclick="enviar('Un millar de block del 15 y 50 bultos de cemento y 30 de cal')" class="bg-green-100 text-green-700 px-3 py-1 rounded-full text-xs hover:bg-green-200">Block+Cemento</button>
        <button onclick="enviar('10m3 concreto, 200 varillas, 21m3 grava y 100 bultos cemento')" class="bg-purple-100 text-purple-700 px-3 py-1 rounded-full text-xs hover:bg-purple-200">Pedido mixto</button>
        <button onclick="enviar('5 cubetas de impermeabilizante y 20 tubos de drenaje')" class="bg-red-100 text-red-700 px-3 py-1 rounded-full text-xs hover:bg-red-200">Acabados</button>
    </div>

    <!-- Input -->
    <div class="p-4 bg-white border-t flex gap-2">
        <input id="input" type="text" placeholder="Escribe tu pedido de materiales..."
               class="flex-1 border rounded-full px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
               onkeydown="if(event.key==='Enter')enviar()">
        <button onclick="enviar()" class="bg-green-600 text-white rounded-full w-10 h-10 flex items-center justify-center hover:bg-green-700">
            &rarr;
        </button>
    </div>

    <script>
        const chat = document.getElementById('chat');
        const input = document.getElementById('input');

        function agregarMensaje(texto, esUsuario) {
            const div = document.createElement('div');
            div.className = 'flex ' + (esUsuario ? 'justify-end' : 'justify-start');
            div.innerHTML = `
                <div class="chat-bubble ${esUsuario ? 'bg-green-100 rounded-2xl rounded-tr-sm' : 'bg-white rounded-2xl rounded-tl-sm'} px-4 py-2 shadow text-sm">
                    ${!esUsuario ? '<div class="font-bold text-green-600 text-xs mb-1">Nico</div>' : ''}
                    ${texto.replace(/\\n/g, '<br>').replace(/\\*([^*]+)\\*/g, '<strong>$1</strong>')}
                    <div class="text-gray-400 text-xs mt-2 text-right">${new Date().toLocaleTimeString('es-MX', {hour:'2-digit',minute:'2-digit'})}</div>
                </div>
            `;
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }

        function mostrarTyping() {
            const div = document.createElement('div');
            div.id = 'typing';
            div.className = 'flex justify-start';
            div.innerHTML = `
                <div class="chat-bubble bg-white rounded-2xl rounded-tl-sm px-4 py-3 shadow flex gap-1">
                    <span class="dot w-2 h-2 bg-gray-400 rounded-full inline-block"></span>
                    <span class="dot w-2 h-2 bg-gray-400 rounded-full inline-block"></span>
                    <span class="dot w-2 h-2 bg-gray-400 rounded-full inline-block"></span>
                </div>
            `;
            chat.appendChild(div);
            chat.scrollTop = chat.scrollHeight;
        }

        function quitarTyping() {
            const t = document.getElementById('typing');
            if (t) t.remove();
        }

        async function enviar(textoDirecto) {
            const texto = textoDirecto || input.value.trim();
            if (!texto) return;
            input.value = '';

            agregarMensaje(texto, true);
            mostrarTyping();

            try {
                const res = await fetch('/sim/chat', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({mensaje: texto})
                });
                const data = await res.json();

                quitarTyping();
                agregarMensaje(data.respuesta, false);

                if (data.comparativa) {
                    setTimeout(() => {
                        agregarMensaje(data.comparativa, false);
                    }, 800);
                }
            } catch(e) {
                quitarTyping();
                agregarMensaje('Error de conexion. Revisa que el servidor este corriendo.', false);
            }
        }

        input.focus();
    </script>

</body>
</html>
"""

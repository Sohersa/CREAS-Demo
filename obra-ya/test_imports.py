"""Test que todos los imports y modulos funcionan correctamente."""
import sys
import traceback

tests = [
    ("Models", "from app.models import *"),
    ("Database", "from app.database import Base, get_db, crear_tablas"),
    ("Config", "from app.config import settings"),
    ("Webhook Router", "from app.routers.webhook import router"),
    ("Admin Router", "from app.routers.admin import router"),
    ("Landing Router", "from app.routers.landing import router"),
    ("Simulador Router", "from app.routers.simulador import router"),
    ("Portal Router", "from app.routers.portal import router"),
    ("Dashboard Router", "from app.routers.dashboard import router"),
    ("Agente Claude", "from app.services.agente_claude import interpretar_pedido"),
    ("Cotizacion Activa", "from app.services.cotizacion_activa import seleccionar_proveedores"),
    ("Parser Respuesta", "from app.services.parser_respuesta_proveedor import parsear_respuesta_proveedor"),
    ("Comparativa Activa", "from app.services.comparativa_activa import armar_comparativa_activa"),
    ("Orden Service", "from app.services.orden_service import crear_orden, avanzar_status"),
    ("Calificacion Service", "from app.services.calificacion_service import calcular_calificacion"),
    ("Incidencia Service", "from app.services.incidencia_service import crear_incidencia"),
    ("Notificaciones", "from app.services.notificaciones import enviar_notificacion_por_status"),
    ("Precio Historico Service", "from app.services.precio_historico_service import registrar_precios_desde_respuesta"),
    ("WhatsApp Service", "from app.services.whatsapp import enviar_mensaje_texto"),
    ("Cotizador", "from app.services.cotizador import cotizar_pedido"),
    ("FastAPI App", "from app.main import app"),
]

passed = 0
failed = 0

for name, import_str in tests:
    try:
        exec(import_str)
        print(f"  OK  {name}")
        passed += 1
    except Exception as e:
        print(f"  FAIL  {name}: {e}")
        traceback.print_exc()
        failed += 1

print(f"\n{'='*40}")
print(f"Resultado: {passed} OK, {failed} FAILED de {len(tests)} tests")
if failed == 0:
    print("Todo funciona correctamente!")
else:
    print(f"HAY {failed} ERRORES QUE ARREGLAR")
    sys.exit(1)

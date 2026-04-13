# ANALISIS CRITICO COMPLETO — Todos los Problemas de ObraYa

**Fecha:** 2026-04-12
**Autor:** Analisis linea-por-linea del codigo real
**Objetivo:** Identificar CADA problema, gap, y variante no cubierta en produccion.

---

## PROCESO 1: RECEPCION DE MENSAJES (webhook.py)

### CRITICO 1.1: Race condition con mensajes simultaneos
**Linea 225:** `background_tasks.add_task(procesar_mensaje, msg, db)` — la sesion de DB (`db`) se pasa al background task, pero FastAPI puede cerrarla antes de que el task termine. Si el usuario manda 2 mensajes rapidos, ambos corren en paralelo con la misma sesion o sesiones que compiten.
**Impacto:** Datos corruptos, ordenes duplicadas, crashes silenciosos.
**Solucion:** Cada background task debe crear su propia sesion con `SessionLocal()`.

### CRITICO 1.2: No hay idempotencia en el webhook
**Problema:** Si WhatsApp reenvia el mismo mensaje (retries por timeout), se procesa DOS VECES. Podria crear 2 pedidos, 2 ordenes, enviar mensajes duplicados al usuario.
**Solucion:** Guardar `message_id` en una tabla y rechazar duplicados. Redis SET con TTL de 5 minutos.

### CRITICO 1.3: El proveedor no recibe notificacion cuando es seleccionado
**Lineas 399-446:** Cuando el usuario elige proveedor, se crea la Orden y se notifica al USUARIO... pero NUNCA se notifica al PROVEEDOR. El proveedor literal no sabe que tiene un pedido confirmado.
**Impacto:** El proveedor nunca prepara el pedido. El cliente espera indefinidamente.
**Solucion:** Agregar `notificar_orden_confirmada_proveedor(db, orden)` que envie WhatsApp al proveedor con los detalles de la orden.

### CRITICO 1.4: "Cancelar" no funciona durante cotizacion
**Lineas 657-676:** `manejar_esperando_cotizaciones()` muestra el texto "escribe cancelar para cancelar" pero NO procesa el comando cancelar. Si el usuario escribe "cancelar", recibe el mismo mensaje de progreso.
**Solucion:** Agregar check: `if "cancelar" in texto.lower(): pedido.status = "cancelado"; db.commit(); enviar "Pedido cancelado"`.

### CRITICO 1.5: municipio_entrega se extrae mal
**Linea 697:** `municipio_entrega=resultado.get("pedido", {}).get("entrega", {}).get("direccion", "").split(",")[0].strip()` — toma el primer segmento de la direccion como municipio. Si la direccion es "Av. Patria 1234, Zapopan", el municipio seria "Av. Patria 1234". INCORRECTO.
**Impacto:** El filtrado geografico de proveedores no funciona correctamente.
**Solucion:** Claude AI debe extraer el municipio como campo separado, o usar reverse geocoding para obtenerlo.

### ALTO 1.6: Sin soporte para imagenes
**Lineas 323-328:** Imagenes se rechazan con "por ahora solo texto, audio y ubicacion". En construccion, los residentes CONSTANTEMENTE mandan fotos de listas de materiales, planos, o fotos del material que necesitan.
**Impacto:** Perdida de pedidos reales.
**Solucion:** Integrar Claude Vision para OCR de imagenes. Claude ya soporta imagenes nativas.

### ALTO 1.7: Sin limite de conversacion incompleta
**Lineas 748-756:** Si Claude devuelve "incompleto", se envia el mensaje y se espera. No hay contador de intentos ni timeout. Un usuario podria ir y venir 20 veces sin completar.
**Solucion:** Limite de 5 intercambios. Despues ofrecer plantilla o escalacion a humano.

### ALTO 1.8: Un solo pedido activo a la vez
**Linea 78:** `detectar_contexto` busca el pedido "cotizando" mas reciente. Si un residente quiere cotizar 2 cosas a la vez (cemento para una obra, varilla para otra), no puede. El segundo pedido queda bloqueado por el primero.
**Solucion:** Permitir multiples pedidos o preguntar "tienes un pedido en proceso, quieres crear otro?"

### MEDIO 1.9: Error generico para excepciones
**Lineas 366-371:** Cualquier error devuelve "tuve un problema procesando tu mensaje". No hay distincion entre error de red, error de DB, error de IA, etc. No hay reintentos.
**Solucion:** Clasificar errores y reintentar los transitorios (red, API timeout).

### MEDIO 1.10: "si" se interpreta como confirmacion en CUALQUIER contexto
**Linea 146:** `es_confirmacion` busca "si" en el texto. Si el usuario responde "si, pero tengo una duda sobre el precio", se interpreta como confirmacion de entrega.
**Solucion:** Hacer matching mas estricto o usar Claude para desambiguar.

---

## PROCESO 2: COTIZACION ACTIVA (cotizacion_activa.py)

### CRITICO 2.1: Sin escalacion cuando NADIE responde
**Scheduler linea 119-138:** Si pasan 30 min y CERO proveedores respondieron, el pedido pasa a "sin_respuesta" y se pregunta al usuario "quieres reintentar?" pero NO se implementa el handler de "SI" en el webhook. El usuario responde "SI" y el sistema lo interpreta como un nuevo pedido.
**Impacto:** El usuario queda atrapado.
**Solucion:** Implementar handler para reintentos. Contactar proveedores diferentes, ampliar zona geografica, o escalar a operador humano.

### CRITICO 2.2: Comparativa se genera dos veces
**Problema:** La comparativa se puede generar tanto desde `manejar_respuesta_proveedor()` (webhook linea 586) como desde `_tarea_auto_comparativa()` (scheduler linea 142). Si ambos detectan "suficientes respuestas" al mismo tiempo, el usuario recibe 2 comparativas.
**Solucion:** Usar un lock o flag en el Pedido (ej: `comparativa_enviada = True`).

### ALTO 2.3: Status "comparando" vs "enviado" inconsistente
**Scheduler linea 159:** Despues de la auto-comparativa, pone status "comparando". Pero webhook linea 592 pone "enviado". El handler de seleccion solo busca status "enviado" (webhook linea 88). Si la comparativa fue generada por el scheduler, el usuario NO puede seleccionar proveedor.
**Impacto:** Usuario recibe comparativa pero no puede elegir.
**Solucion:** Unificar a un solo status "enviado" en ambos caminos.

### ALTO 2.4: Respuestas tardias de proveedores se pierden
**Webhook linea 549:** Busca solicitudes con status "enviada" o "recordatorio_enviado". Si el proveedor responde DESPUES de que su solicitud fue marcada "sin_respuesta" (timeout), la respuesta se pierde. El proveedor recibe "no tengo solicitudes pendientes".
**Impacto:** Perder precios potencialmente buenos. Proveedor se frustra.
**Solucion:** Aceptar respuestas tardias (status "sin_respuesta") y si la orden no se creo aun, incluirlas.

### ALTO 2.5: Sin validacion de precios absurdos
**Problema:** Si un proveedor responde "cuesta $5,000,000 el bulto de cemento" o "$0.01", el sistema lo registra sin cuestionarlo. El outlier detection solo funciona post-facto en PrecioHistorico.
**Solucion:** Validar contra precio_referencia del catalogo. Si es >5x o <0.2x, preguntar al proveedor "estas seguro que el precio es $X por Y?"

### ALTO 2.6: Template de WhatsApp no implementado realmente
**Codigo:** `enviar_mensaje_template()` existe pero el webhook solo usa `enviar_mensaje_texto()`. Los templates de WhatsApp son OBLIGATORIOS para mensajes fuera de la ventana de 24 horas. Si un proveedor no ha hablado con Nico en 24h, el mensaje de texto sera rechazado por Meta.
**Impacto:** Cotizaciones no llegan a proveedores inactivos.
**Solucion:** Usar `enviar_mensaje_template()` como primer intento, texto como fallback dentro de ventana 24h.

### MEDIO 2.7: Categorias de proveedor vs pedido no siempre matchean
**Problema:** Si el usuario pide "pintura vinilica blanca" y Claude la categoriza como "acabados", pero el proveedor tiene categoria "pintura", no hay match. El proveedor tiene el producto pero no es contactado.
**Solucion:** Matching mas flexible — incluir subcategorias, sinonimos de categorias.

### MEDIO 2.8: Sin tracking de tasa de respuesta por hora del dia
**Problema:** Si mandamos cotizaciones a las 10pm, la tasa de respuesta sera 0%. Desperdiciamos mensajes.
**Solucion:** Respetar horarios de atencion del proveedor/vendedor. No enviar fuera de horario.

---

## PROCESO 3: SELECCION DE PROVEEDOR

### CRITICO 3.1: No hay timeout de seleccion
**Problema:** Despues de enviar la comparativa, el sistema espera indefinidamente a que el usuario elija. Si el usuario no responde en 3 dias, el pedido queda en "enviado" para siempre, bloqueando cualquier pedido nuevo del usuario.
**Impacto:** Usuario atrapado. Cotizaciones de proveedores ya no son validas.
**Solucion:** Timeout de 24 horas. Despues: "Tu comparativa expiro. Los precios pueden haber cambiado. Quieres que vuelva a cotizar?"

### ALTO 3.2: No hay negociacion
**Problema:** Si el usuario dice "preguntale al proveedor 1 si me hace descuento", el sistema no sabe que hacer. Le muestra las mismas opciones.
**Solucion:** Detectar intent de negociacion y reenviar al proveedor: "El cliente pregunta si hay descuento por volumen/pago de contado."

### ALTO 3.3: Cotizaciones sin vigencia real
**Problema:** La cotizacion tiene campo `vigencia` pero nunca se valida. Un usuario podria seleccionar una cotizacion de hace 3 dias cuyos precios ya cambiaron (especialmente acero, concreto que fluctuan diario).
**Solucion:** Validar vigencia al seleccionar. Si expiro: "Esta cotizacion tiene X dias. Los precios podrian haber cambiado. Quieres confirmar o recotizar?"

### MEDIO 3.4: No se puede comparar items individuales
**Problema:** La comparativa muestra totales. El usuario no puede decir "quiero el cemento del proveedor 1 y la varilla del proveedor 2".
**Nota:** Esto es un feature avanzado pero comun en construccion.

---

## PROCESO 4: APROBACION CORPORATIVA

### CRITICO 4.1: La orden se crea ANTES de la aprobacion
**Webhook lineas 402-410:** Primero crea la orden (`crear_orden`), luego verifica si necesita aprobacion. Si necesita aprobacion, la orden ya existe en status "confirmada". Si la aprobacion es rechazada, la orden queda "confirmada" sin cancelarse.
**Impacto:** Ordenes rechazadas que siguen activas. El proveedor podria ser notificado (si se corrige 1.3) de un pedido que fue rechazado.
**Solucion:** Crear la orden en status "pendiente_aprobacion" antes de confirmarla. Solo mover a "confirmada" cuando se aprueba.

### CRITICO 4.2: Rechazo no cancela la orden
**Webhook lineas 634-654:** Cuando un aprobador rechaza, se actualiza la Aprobacion pero NO se cancela la Orden. La orden sigue activa en "confirmada".
**Solucion:** `rechazar_aprobacion()` debe tambien llamar `cancelar_orden(db, orden_id, "Rechazada por aprobador")`.

### ALTO 4.3: Aprobador responde "si dale" en lugar de "APROBAR 42"
**Lineas 175-181:** Solo acepta el formato exacto `APROBAR {numero}`. Un director que recibe el mensaje y responde "si, aprobado", "dale", "va", "ok autorizado" no sera entendido.
**Impacto:** Frustracion del aprobador. Retraso de compra.
**Solucion:** Usar Claude para interpretar respuestas naturales en contexto de aprobacion.

### ALTO 4.4: Sin notificacion al solicitante cuando expira
**Problema:** `verificar_expiradas()` marca la aprobacion como "expirada" pero no notifica ni al solicitante ni al aprobador. El residente no sabe que su compra fue bloqueada.
**Solucion:** Enviar WhatsApp: "Tu solicitud de aprobacion para $X expiro porque no fue respondida en 24h. Quieres reenviarla?"

### ALTO 4.5: Sin aprobacion desde la web implementada end-to-end
**Problema:** El portal de aprobaciones muestra pendientes y tiene botones, pero no esta vinculado al flujo de notificacion. Si alguien aprueba desde la web, no se envia WhatsApp al solicitante (el endpoint API no llama `componer_mensaje_resultado`).
**Solucion:** Los endpoints `/aprobaciones/{id}/aprobar` y `/rechazar` deben notificar por WhatsApp.

### MEDIO 4.6: Dos aprobadores pueden aprobar la misma solicitud
**Problema:** Si dos personas con permisos leen el WhatsApp y ambas escriben "APROBAR 42", la segunda falla silenciosamente (la solicitud ya no esta "pendiente"). Pero no hay feedback claro.
**Solucion:** Segundo aprobador recibe: "Esta solicitud ya fue aprobada por [nombre]."

---

## PROCESO 5: ORDEN Y ENTREGA

### CRITICO 5.1: Proveedor NUNCA es notificado de la orden (repetir 1.3)
**El problema mas grave del sistema.** Se crea la orden, se notifica al usuario, pero el proveedor no recibe nada. Sin corregir esto, NINGUNA orden funciona en produccion.

### CRITICO 5.2: No hay escalacion por proveedor fantasma
**Escenario del usuario:** Proveedor acepto cotizacion, usuario selecciono, pero proveedor no contesta. Pasan 4h, 12h, 24h. El agente proactivo manda recordatorios pero el proveedor sigue sin responder.
**Problema actual:** Solo se registran warnings en logs. No hay accion concreta.
**Lo que deberia pasar:**
  - 4h sin respuesta: Alerta al cliente "Tu proveedor no ha confirmado preparacion. Estamos siguiendo."
  - 8h sin respuesta: Llamar por telefono al proveedor (flag para operador humano).
  - 12h sin respuesta: Alerta al cliente "Hay un retraso. Quieres que contacte otro proveedor?"
  - 24h sin respuesta: Auto-cancelar orden + auto-recotizar con los otros proveedores que habian respondido.
  - En todo momento: Dashboard de "ordenes en riesgo" para el admin.

### CRITICO 5.3: No hay forma de que el proveedor actualice el status
**Problema:** El proveedor no tiene un mecanismo en WhatsApp para decir "PREPARANDO 42" o "EN CAMINO 42". El webhook no reconoce estos comandos de proveedores — solo reconoce respuestas a SOLICITUDES de cotizacion.
**Impacto:** El unico que puede cambiar el status es el admin desde el panel. No es escalable.
**Solucion:** Agregar handler en webhook: si un proveedor manda "LISTO {id}" o "EN CAMINO {id}", avanzar el status de la orden.

### ALTO 5.4: Entrega parcial no esta soportada
**Problema:** Si de 15m3 de concreto llegan 10m3 y faltan 5m3 (muy comun — el segundo viaje viene despues), no hay forma de registrarlo. El usuario confirma "RECIBIDO" o reporta "PROBLEMA". No hay "PARCIAL".
**Impacto:** El usuario tiene que reportar como problema algo que es normal. O confirma como entregado cuando aun falta material.
**Solucion:** Agregar opcion "PARCIAL {id} llego X de Y". Crear sub-orden para el remanente.

### ALTO 5.5: Fecha de entrega prometida nunca se registra
**Problema:** `Orden.fecha_entrega_prometida` existe en el modelo pero NUNCA se llena en `crear_orden()` (linea 47). Siempre es NULL.
**Impacto:** El agente proactivo que alerta por retrasos (`alertar_retraso_entrega`) nunca se dispara porque filtra por `fecha_entrega_prometida.isnot(None)`.
**Solucion:** Extraer tiempo_entrega de la cotizacion del proveedor y calcular fecha_entrega_prometida al crear la orden.

### ALTO 5.6: Confirmacion de entrega demasiado facil de activar
**Linea 466:** Si el usuario manda "si" o "bien" cuando tiene una orden en "en_obra", se confirma como entregada. Pero el material podria no haber llegado aun — alguien cambio el status a "en_obra" por error.
**Solucion:** Pedir confirmacion explicita: "Confirma que recibiste TODOS los materiales de la orden #42 respondiendo RECIBIDO."

### MEDIO 5.7: Timeline no distingue quien hizo cada cambio
**Problema:** `SeguimientoEntrega.origen` registra "admin", "usuario", "proveedor", "agente" pero no el ID ni nombre especifico. Si hay 3 admins, no sabes cual movio la orden.
**Solucion:** Agregar campo `actor_id` y `actor_nombre`.

### MEDIO 5.8: Sin fotos de evidencia de entrega
**Problema:** No hay forma de que el chofer mande foto del material entregado, ni que el usuario mande foto de lo que recibio. En disputas, no hay evidencia.
**Solucion:** Cuando el proveedor manda imagen durante una orden activa, guardarla como evidencia.

---

## PROCESO 6: PAGOS

### CRITICO 6.1: STRIPE_SECRET_KEY no esta configurado
**Estado actual:** No hay API key de Stripe en Railway. Todo el flujo de pagos es inoperativo.
**Impacto:** No se puede cobrar nada.

### ALTO 6.2: No hay facturacion (CFDI)
**Problema:** En Mexico, las empresas constructoras NECESITAN factura (CFDI) para deducir impuestos. Sin factura, las empresas no van a usar el sistema.
**Solucion:** Integrar con proveedor de facturacion (Facturapi, SatWS) para emitir CFDI por cada pago.

### ALTO 6.3: No hay soporte para pago en efectivo o transferencia
**Problema:** Muchas compras de materiales en Mexico se pagan en efectivo o transferencia bancaria. El sistema solo soporta Stripe (tarjeta).
**Solucion:** Agregar opciones de pago: transferencia SPEI (con verificacion) y efectivo contra entrega.

### ALTO 6.4: Webhook de Stripe sin retry logic
**Lineas 132-159:** Si el webhook de Stripe falla (DB down, server crash), el pago quedo en Stripe pero no en nuestra BD. No hay reconciliacion.
**Solucion:** Tarea programada que consulte sesiones de Stripe abiertas y verifique si fueron pagadas.

### MEDIO 6.5: Simulacion de pago disponible en produccion
**Linea 169:** El check `settings.ENVIRONMENT == "production"` protege el endpoint de simulacion, pero la variable ENVIRONMENT podria no estar configurada (default vacio = no es "production" = simulacion habilitada).
**Solucion:** Invertir la logica: solo permitir si explicitamente es "development".

### MEDIO 6.6: No hay manejo de disputas/chargebacks
**Problema:** Si un cliente hace chargeback en Stripe, no se notifica internamente ni se bloquea la cuenta.

---

## PROCESO 7: PRESUPUESTOS

### ALTO 7.1: Consumo presupuestal no vinculado a partidas individuales
**Lineas 86-104 de orden_service.py:** El auto-consumo solo suma al `gastado_total` general del presupuesto, pero NO a las partidas individuales. Las alertas de 50/80/100% por partida nunca se disparan automaticamente.
**Impacto:** Las alertas granulares de presupuesto son inutiles.
**Solucion:** Mapear items de la orden contra partidas del presupuesto y registrar consumo por partida.

### ALTO 7.2: Bloqueo de partida se puede saltar
**Problema:** La partida se bloquea al 100% pero el pedido via WhatsApp NO verifica disponibilidad presupuestal. Solo se verifica desde el portal web.
**Solucion:** Verificar disponibilidad presupuestal en `crear_orden()` antes de confirmar.

### MEDIO 7.3: Sin presupuesto multi-empresa
**Problema:** El presupuesto esta ligado a usuario_id, no a empresa_id. Si 3 residentes de la misma empresa tienen presupuestos separados, no se consolida el gasto real de la obra.
**Solucion:** Vincular presupuesto a empresa + obra, no a usuario individual.

### MEDIO 7.4: Precios estimados vs reales divergen
**Problema:** El presupuesto se crea con `precio_unitario_estimado` pero las compras reales pueden ser muy diferentes. No hay alerta cuando el precio real es significativamente mayor al estimado.

---

## PROCESO 8: CREDIT SCORING

### ALTO 8.1: Score nunca se recalcula automaticamente
**Problema:** `calcular_score()` existe pero solo se llama manualmente desde el endpoint `/credito/recalcular/{id}` o al confirmar pago. Los campos `total_gastado`, `total_pedidos_completados`, etc. no se actualizan consistentemente.
**Solucion:** Recalcular al menos los campos basicos en cada orden completada.

### MEDIO 8.2: Nuevas empresas grandes penalizadas
**Problema:** Una constructora con 100 empleados que se registra hoy tiene score 50 (sin historial). No puede acceder a credito. Pero es obviamente solvente.
**Solucion:** Permitir override manual del score para empresas verificadas. Agregar campo `score_manual_override`.

### MEDIO 8.3: Un pago tarde destruye el score
**Problema:** Si una empresa tiene 50 pagos a tiempo y 1 tarde (por error bancario), su score baja desproporcionadamente.
**Solucion:** Usar promedio movil, no total acumulado. Perdonar 1 pago tarde si el historial es excelente.

---

## PROCESO 9: CALIFICACIONES

### ALTO 9.1: Calificacion auto-calculada requiere fecha_entrega_prometida
**Problema:** La puntualidad se calcula comparando `fecha_entrega_prometida` vs `fecha_entrega_real`. Pero como vimos en 5.5, `fecha_entrega_prometida` nunca se llena. La calificacion de puntualidad siempre sera 5.0 (sin datos = perfecto).
**Impacto:** Proveedores impuntuales no son penalizados.

### ALTO 9.2: Rating de 1 estrella sin mecanismo de disputa
**Problema:** Si un cliente da 1 estrella injustamente, el proveedor no tiene forma de responder o disputar.
**Solucion:** Notificar al proveedor cuando recibe calificacion baja. Permitir respuesta.

### MEDIO 9.3: Solicitud de calificacion a las 24h exactas puede fallar
**Agente proactivo:** Busca ordenes entregadas entre 24h y 25h atras. Si el scheduler se retrasa o el servidor se reinicia, la ventana se pierde y nunca se pide calificacion.
**Solucion:** Usar flag `calificacion_solicitada` en la orden. Buscar todas las ordenes entregadas sin calificacion solicitada.

---

## PROCESO 10: GESTION DE EQUIPOS

### ALTO 10.1: No hay forma de desactivar un empleado que renuncio
**Problema:** Desde el Hub se puede crear miembros pero no desactivarlos desde la UI. Si un residente renuncia, sigue pudiendo pedir materiales a nombre de la empresa.
**Solucion:** Agregar boton de desactivar en la UI y endpoint PUT.

### ALTO 10.2: Vendedor y proveedor comparten espacio de telefonos
**Problema:** Si un vendedor y un cliente tienen el mismo numero (posible si alguien trabaja para proveedor Y compra para si mismo), el sistema siempre lo tratara como proveedor (el check de proveedor va ANTES del de contexto en el webhook).
**Solucion:** Preguntar: "Estas respondiendo como proveedor o haciendo un pedido personal?"

### MEDIO 10.3: Sin auditoria de cambios de roles
**Problema:** Si alguien cambia el limite de aprobacion de un miembro, no hay log. No se sabe quien lo cambio ni cuando.

---

## PROCESO 11: INTELIGENCIA DE PRECIOS

### ALTO 11.1: Precios no se registran desde cotizacion estatica
**Problema:** `cotizador.py` genera cotizaciones de la BD pero no registra precios en PrecioHistorico. Solo `cotizacion_activa.py` registra precios.
**Impacto:** La base de precios solo crece con cotizaciones reales de WhatsApp, no con consultas de BD.

### MEDIO 11.2: Sin ajuste por inflacion/estacionalidad
**Problema:** Los precios se muestran crudos. No hay contexto de "este precio subio 15% desde el mes pasado" o "el acero siempre sube en temporada de lluvias".

### MEDIO 11.3: Sin deteccion de proveedores que inflan precios
**Problema:** Si un proveedor siempre cotiza 30% mas caro que el promedio, no hay alerta automatica para investigar.

---

## PROCESO 12: COMUNICACION WHATSAPP

### CRITICO 12.1: Sin cola de mensajes (message queue)
**Problema:** Todos los mensajes se envian directamente via httpx. Si la API de WhatsApp esta caida, el mensaje se pierde. No hay retry, no hay cola.
**Impacto:** Notificaciones criticas (aprobaciones, alertas de entrega) se pierden.
**Solucion:** Cola de mensajes (Redis Queue, Celery, o al menos una tabla `mensajes_pendientes`).

### ALTO 12.2: Ventana de 24 horas de WhatsApp
**Problema:** WhatsApp Business API solo permite mensajes de texto libre dentro de las 24h despues del ultimo mensaje del usuario. Despues de 24h, solo templates aprobados.
**Impacto:** Si un proveedor no ha hablado con Nico en 2 dias, la solicitud de cotizacion sera rechazada por Meta.
**Estado actual:** `enviar_mensaje_template` existe pero NO se usa en el flujo de cotizacion.

### ALTO 12.3: Rate limits de WhatsApp
**Problema:** Meta tiene limites de mensajes por hora/dia. Si mandamos a 20 proveedores x 10 pedidos = 200 mensajes, podemos ser throttled.
**Solucion:** Implementar rate limiting interno. Maxximo X mensajes por minuto.

### ALTO 12.4: Sin canal de backup (email/SMS)
**Problema:** Si WhatsApp falla completamente, no hay forma alternativa de comunicar. Las aprobaciones, alertas, cotizaciones — todo depende de WhatsApp.
**Solucion:** Para usuarios con email, enviar notificaciones criticas tambien por email. Para aprobadores, permitir aprobacion por email.

### MEDIO 12.5: Sin horario de "no molestar"
**Problema:** El agente proactivo puede enviar alertas a las 2am. Un recordatorio de "tu pedido lleva 4h en confirmada" a las 3am es molesto e inutil.
**Solucion:** Respetar horario laboral (7am-8pm). Encolar mensajes fuera de horario para enviar en la manana.

---

## PROCESO 13: AGENTE PROACTIVO

### ALTO 13.1: Sin control de spam
**Problema:** Las funciones del agente proactivo NO verifican si ya enviaron un mensaje similar recientemente. El check de "solo a las 4h y 12h" usa rangos de 0.3h, pero si el scheduler se retrasa, podria enviar 2 veces.
**Solucion:** Usar flag en la orden: `ultimo_recordatorio_at`, `recordatorios_proveedor_enviados`. No enviar si ya se envio en las ultimas 3h.

### ALTO 13.2: Recordatorio de cotizacion duplica el del scheduler
**Problema:** `recordar_cotizaciones_pendientes()` en el agente proactivo Y `_tarea_recordatorios_proveedores()` en el scheduler hacen lo mismo — recordar a proveedores que no contestan. Pueden enviar mensajes duplicados.
**Solucion:** Eliminar uno de los dos. El del scheduler es mas robusto.

### MEDIO 13.3: Sin escalacion a humano
**Problema:** El agente envia alertas pero nunca escala a un operador humano. No hay concepto de "esta situacion es tan grave que necesita intervencion manual".
**Solucion:** Panel de "alertas criticas" en el Hub. Si una orden lleva >24h estancada, crear alerta roja visible.

### MEDIO 13.4: Sin metricas del agente
**Problema:** No hay forma de saber cuantas alertas envio el agente, cuantas fueron utiles, cuantas resultaron en accion del usuario.
**Solucion:** Tabla `alertas_agente` con tipo, resultado, timestamp.

---

## PROCESO 14: INFRAESTRUCTURA Y DATOS

### CRITICO 14.1: SQLite en produccion
**Problema:** SQLite no soporta conexiones concurrentes bien. Con multiples usuarios enviando mensajes simultaneos + scheduler + agente proactivo, habra lock contention.
**Solucion:** Migrar a PostgreSQL (Railway lo soporta nativo).

### ALTO 14.2: Sin backups automaticos
**Problema:** Si el servidor de Railway se cae o el disco se corrompe, se pierde toda la data. SQLite es un archivo local.
**Solucion:** Backup periodico a S3 o PostgreSQL con backups automaticos.

### ALTO 14.3: Sin monitoreo ni alertas de sistema
**Problema:** Si el scheduler deja de correr, si la API de WhatsApp falla, si la BD se llena — nadie se entera hasta que un cliente se queja.
**Solucion:** Health checks que verifiquen: scheduler activo, ultimo mensaje enviado < 1h, API keys validas.

### MEDIO 14.4: Logs solo en memoria
**Problema:** `log_buffer` guarda los ultimos 200 logs en memoria. Si el servidor se reinicia, se pierden.
**Solucion:** Persistir logs criticos en BD o servicio externo.

---

## RESUMEN: PRIORIDADES DE CORRECCION

### MUST FIX (Sin esto no funciona en produccion):
1. **Notificar al proveedor cuando es seleccionado** (5.1/1.3)
2. **Idempotencia del webhook** (1.2)
3. **Race condition de DB sessions** (1.1)
4. **Status "comparando" vs "enviado" inconsistente** (2.3)
5. **Orden se crea antes de aprobacion** (4.1)
6. **Rechazo no cancela la orden** (4.2)
7. **fecha_entrega_prometida nunca se llena** (5.5)
8. **Proveedor no puede actualizar status por WhatsApp** (5.3)
9. **Cancelar no funciona durante cotizacion** (1.4)
10. **Cola de mensajes para WhatsApp** (12.1)
11. **SQLite → PostgreSQL** (14.1)

### SHOULD FIX (Afecta calidad de servicio):
12. Escalacion por proveedor fantasma (5.2)
13. Soporte para imagenes (1.6)
14. Timeout de seleccion de proveedor (3.1)
15. Aprobador puede responder en lenguaje natural (4.3)
16. Templates de WhatsApp para mensajes fuera de ventana 24h (12.2)
17. Consumo presupuestal por partida (7.1)
18. Facturacion CFDI (6.2)
19. Pago en efectivo/transferencia (6.3)
20. Horario de no molestar (12.5)
21. Aprobaciones expiradas notifican al solicitante (4.4)
22. Duplicacion de comparativas (2.2)
23. Respuestas tardias de proveedores (2.4)

### NICE TO HAVE (Mejora la experiencia):
24. Entrega parcial (5.4)
25. Negociacion de precios (3.2)
26. Canal backup email (12.4)
27. Fotos de evidencia (5.8)
28. Metricas del agente (13.4)
29. Auditoria de cambios de roles (10.3)
30. Deteccion de inflacion de precios (11.3)

**Total: 30 problemas reales, 11 criticos, 12 altos, 7 medios.**

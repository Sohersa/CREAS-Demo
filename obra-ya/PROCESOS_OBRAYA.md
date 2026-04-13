# ObraYa -- Mapa Completo de Procesos

---

## 1. Vision General

### 1.1 Que es ObraYa

ObraYa es una plataforma de abastecimiento de materiales de construccion que opera 100% por WhatsApp. A diferencia de un marketplace con precios estaticos, ObraYa funciona como un agente inteligente ("Nico") que contacta proveedores en tiempo real, solicita cotizaciones por WhatsApp, compara respuestas y permite al comprador elegir la mejor opcion -- todo sin salir de la conversacion. El residente de obra pide material desde el campo, Nico hace el trabajo de llamar a 20 proveedores, y en minutos tiene una comparativa real con precios del momento.

### 1.2 Arquitectura Tecnica

```
                    +-------------------+
                    |   WhatsApp Cloud  |
                    |   API (Meta)      |
                    +--------+----------+
                             |
                    +--------v----------+
                    |   FastAPI Backend  |
                    |   (Python 3.11+)  |
                    +--------+----------+
                             |
          +------------------+------------------+
          |                  |                  |
  +-------v-------+  +------v------+  +--------v--------+
  |   SQLite DB   |  | Claude AI   |  |  Stripe Payments|
  |  (SQLAlchemy) |  | (Anthropic) |  |  (Checkout)     |
  +---------------+  +------+------+  +-----------------+
                             |
                    +--------v----------+
                    |   Groq Whisper    |
                    |   (Audio -> Text) |
                    +-------------------+
```

**Stack principal:**
- **Backend:** FastAPI (Python) con SQLAlchemy ORM
- **Base de datos:** SQLite (desarrollo), migracion a PostgreSQL en produccion
- **Mensajeria:** WhatsApp Cloud API (Meta) + Twilio como fallback
- **IA:** Anthropic Claude (interpretacion de pedidos, parseo de respuestas)
- **Voz:** Groq Whisper (transcripcion de notas de voz)
- **Pagos:** Stripe Checkout (tarjeta de credito/debito)
- **Geocoding:** Nominatim/OpenStreetMap (ubicacion GPS a direccion)
- **Auth Web:** Google OAuth (portales web)

### 1.3 Actores del Sistema

| Actor | Descripcion | Canal principal |
|-------|-------------|-----------------|
| **Cliente (Comprador)** | Persona que necesita materiales de construccion | WhatsApp |
| **Residente de obra** | Personal en campo que pide materiales dia a dia | WhatsApp |
| **Superintendente** | Supervisa varios residentes, puede aprobar compras | WhatsApp |
| **Compras** | Departamento de adquisiciones de la constructora | WhatsApp / Web |
| **Director** | Maximo nivel de aprobacion corporativa | WhatsApp / Web |
| **Proveedor** | Empresa que vende materiales (ferreteria, cementera, etc.) | WhatsApp / Web |
| **Vendedor** | Persona especifica dentro de un proveedor que atiende | WhatsApp |
| **Agente Nico (IA)** | Agente inteligente que orquesta todo el flujo | Automatico |

---

## 2. Proceso Principal: Pedido de Materiales

### 2.1 Inicio del Pedido (WhatsApp)

**Entradas soportadas:**
- **Texto:** "Necesito 15 metros cubicos de concreto fc 250 para manana en Zapopan"
- **Audio:** Nota de voz que se transcribe automaticamente con Groq Whisper
- **Ubicacion:** Pin de GPS que se convierte a direccion via reverse geocoding (Nominatim)

**Flujo de deteccion de contexto:**

Antes de procesar el mensaje, el sistema detecta en que estado se encuentra el usuario:

```
Mensaje entrante
      |
      v
  Es proveedor? ----SI----> manejar_respuesta_proveedor()
      |NO
      v
  Es APROBAR/RECHAZAR? --SI--> manejar_aprobacion() / manejar_rechazo()
      |NO
      v
  Detectar contexto del usuario:
      |
      +-- Pedido en "cotizando"    --> manejar_esperando_cotizaciones()
      +-- Pedido en "enviado"      --> manejar_seleccion_proveedor()
      +-- Orden en "en_obra"       --> manejar_confirmacion_entrega()
      +-- Orden activa (otra)      --> manejar_orden_activa()
      +-- Nada activo              --> manejar_nuevo_pedido()
```

**Interpretacion por Claude AI:**

El agente Claude analiza el mensaje del usuario y extrae:
- **Items:** producto, cantidad, unidad, categoria, especificaciones (resistencia, calibre, tipo)
- **Entrega:** direccion, municipio, fecha, horario
- **Status:** "completo" (tiene todo para cotizar) o "incompleto" (falta info)

Si el pedido esta incompleto, Nico responde pidiendo lo que falta (ej: "Me dices la direccion de entrega?").

### 2.2 Cotizacion Activa (Real-time)

Este es el corazon de ObraYa. NO es un catalogo estatico -- es cotizacion en vivo.

**Paso 1: Seleccion de proveedores (hasta 20)**

```
Criterios de seleccion (en orden de prioridad):
  1. Categorias: el proveedor maneja al menos 1 categoria del pedido
  2. Activo: proveedor habilitado en el sistema
  3. WhatsApp: tiene numero de WhatsApp registrado
  4. Geografia: bonus por cercania al punto de entrega
     - Mismo municipio: +5.0 puntos
     - Misma zona metropolitana: +3.0 puntos
     - Otra ciudad: -2.0 puntos
  5. Calificacion: mejor rating tiene prioridad
  6. Pedidos cumplidos: mas experiencia = mas arriba
  7. Tiempo de respuesta: mas rapido = mas arriba
```

**Zonas metropolitanas soportadas:**
- Guadalajara (Zapopan, Tlaquepaque, Tonala, Tlajomulco, El Salto, etc.)
- Monterrey (San Pedro, Apodaca, Guadalupe, Santa Catarina, etc.)
- CDMX (Naucalpan, Tlalnepantla, Ecatepec, etc.)
- Mazatlan, Culiacan, Leon, Queretaro, Puebla, Merida, Tijuana, Aguascalientes

**Paso 2: Envio de mensaje al proveedor**

```
Hola, buen dia. Soy Nico de ObraYa.

Tengo un cliente que necesita los siguientes materiales:

  - 15 m3 de concreto (fc 250)
  - 20 varillas de 3/8

Entrega en: Zapopan
Direccion: Av. Patria 1234

Me podrias pasar tu mejor precio con flete incluido?
Si puedes indicar tiempo de entrega, mejor.

Gracias!
```

**Routing inteligente vendedor/proveedor:**

```
Para cada proveedor:
  1. Buscar vendedor activo + disponible con menor tiempo de respuesta
  2. Si hay vendedor --> enviar a su WhatsApp personal
  3. Si no hay vendedor --> enviar al WhatsApp general del proveedor
```

El sistema intenta primero enviar un template de WhatsApp (funciona fuera de ventana 24h). Si el template no esta aprobado, envia texto libre como fallback.

**Paso 3: Espera y recordatorios**

```
Tiempo 0min  --> Solicitud enviada
Tiempo 15min --> Primer recordatorio a proveedores sin respuesta
Tiempo 25min --> Segundo recordatorio (maximo 2 recordatorios)
Tiempo 30min --> Timeout: se arma comparativa con lo que haya
```

Mensaje de recordatorio:
```
Hola, soy Nico de ObraYa.
Te habia mandado una solicitud de cotizacion hace rato:
[resumen del pedido]
Todavia tienes chance de cotizar?
Si no manejas algun material, no hay problema, dime.
```

**Paso 4: Parseo de respuestas por IA**

Cuando un proveedor responde (texto libre por WhatsApp), Claude AI parsea:
- `tiene_precio`: si incluye precio o no
- `precio_total`: monto total cotizado
- `desglose`: lista de items con precio unitario, cantidad, unidad, subtotal
- `incluye_flete`: si el precio incluye flete
- `costo_flete`: costo del flete por separado
- `tiempo_entrega`: "2 horas", "manana", etc.
- `notas`: condiciones adicionales
- `sin_stock`: si dijo que no tiene material

**Paso 5: Registro de precios historicos**

Cada respuesta de proveedor se registra automaticamente en la tabla `PrecioHistorico`:
- Producto normalizado contra catalogo maestro
- Precio unitario + flete prorrateado = precio efectivo
- Zona, fecha, dia de la semana, mes, trimestre
- Deteccion de outliers (precio > 3x o < 0.3x del promedio)

### 2.3 Comparativa de Precios

Cuando hay suficientes respuestas (minimo 1), se arma la comparativa:

```
Comparativa de precios para tu pedido #42:

  1. Materiales Zapopan -- $18,500
     - 15 m3 concreto fc250: $1,100/m3
     - Flete incluido
     - Entrega: 2 horas

  2. Concretos del Bajio -- $19,200
     - 15 m3 concreto fc250: $1,180/m3
     - Flete: $1,500
     - Entrega: manana 8am

Responde con el NUMERO del proveedor que prefieras (ej: 1)
```

El usuario responde "1", "el primero", "el mas barato", etc. El sistema interpreta respuestas naturales.

### 2.4 Cotizacion Estatica (Fallback)

Si no hay proveedores con WhatsApp o mientras se espera respuestas reales, se generan cotizaciones de la base de datos:

**Motor de cotizacion (cotizador.py):**

```
1. Usuario dice "varilla del tres octavos"
2. Buscar en aliases_producto --> catalogo_id = 6
3. Buscar todos los productos con catalogo_id = 6
4. Agrupar por proveedor, calcular subtotales
5. Sumar flete estimado por municipio
6. Ordenar por precio total
```

**Calculo de flete por municipio (desde centro GDL):**

| Municipio | Flete estimado |
|-----------|---------------|
| Guadalajara | $800 |
| Tlaquepaque | $1,000 |
| Zapopan | $1,200 |
| Tonala | $1,500 |
| Tlajomulco | $1,800 |
| El Salto | $2,000 |
| Ixtlahuacan | $2,500 |

Reglas especiales:
- Mismo municipio proveedor/entrega: flete al 50%
- Proveedor grande con subtotal > $30,000: flete gratis

---

## 3. Proceso de Aprobacion Corporativa

### 3.1 Verificacion de Limites

```
Compra solicitada
      |
      v
  Usuario pertenece a empresa? --NO--> Compra directa (sin aprobacion)
      |SI
      v
  Empresa requiere aprobacion? --NO--> Compra directa
      |SI
      v
  Monto <= limite_sin_aprobacion de la empresa? --SI--> Compra directa
      |NO
      v
  El usuario puede auto-aprobar este monto? --SI--> Compra directa
      |NO
      v
  REQUIERE APROBACION --> solicitar_aprobacion()
```

**Jerarquia de roles y limites (ejemplo demo):**

| Rol | Puede pedir | Puede aprobar | Puede pagar | Limite aprobacion |
|-----|------------|---------------|-------------|-------------------|
| Residente | Si | No | No | $50,000 |
| Superintendente | Si | Si | No | $150,000 |
| Compras | Si | Si | Si | $500,000 |
| Director | Si | Si | Si | Sin limite |

### 3.2 Solicitud de Aprobacion

Al crearse la solicitud:
1. Se crea registro `Aprobacion` con status "pendiente" y expiracion en 24 horas
2. Se buscan todos los miembros de la empresa con `puede_aprobar = True`
3. Solo se notifica a aprobadores cuyo limite_aprobacion >= monto de la orden
4. Se envia WhatsApp a cada aprobador con contexto completo

**Mensaje al aprobador:**

```
*Solicitud de Aprobacion*

*Detalle del pedido:*
  - Concreto fc250 x15 m3 -- $16,500
  - Varilla 3/8 x20 pza -- $2,000
  *Total: $18,500 MXN*

*Solicitante:* Juan Perez (residente)
*Entrega:* Av. Patria 1234, Zapopan

*Consumo acumulado:* $125,000 de $500,000 limite

*Alerta de presupuesto:*
La obra "Torre Norte" lleva 65% consumido
($325,000 de $500,000)
Este pedido llevaria el consumo a 69%

Para responder:
  APROBAR 42 -- autorizar compra
  RECHAZAR 42 [motivo] -- rechazar

Expira en 24 horas.
```

### 3.3 Aprobacion / Rechazo

**Via WhatsApp:**
- `APROBAR 42` --> aprueba orden #42
- `APROBAR 42 adelante con todo` --> aprueba con nota
- `RECHAZAR 42 muy caro, busca otra opcion` --> rechaza con motivo

**Via portal web:** boton de aprobar/rechazar en `/aprobaciones/`

**Validaciones al aprobar:**
- El aprobador debe pertenecer a la misma empresa
- Debe tener `puede_aprobar = True` y estar activo
- Su `limite_aprobacion` debe ser >= al monto de la orden

**Expiracion:**
- Aprobaciones pendientes por mas de 24 horas se marcan como "expirada"
- Un scheduler periodico ejecuta `verificar_expiradas()`

**Notificacion al solicitante:**

```
(Aprobada)
*Compra aprobada!*
Orden #42 -- $18,500 MXN
Aprobada por: Carlos Gonzalez
Tu pedido se esta procesando.

(Rechazada)
*Compra rechazada*
Orden #42 -- $18,500 MXN
Rechazada por: Carlos Gonzalez
Motivo: muy caro, busca otra opcion
Si necesitas ajustar el pedido, mandame mensaje.
```

---

## 4. Proceso de Orden y Entrega

### 4.1 Creacion de Orden

Cuando el usuario elige un proveedor:

```
Usuario responde "1"
      |
      v
  Crear Orden desde Cotizacion:
    - proveedor_id
    - items (JSON)
    - total
    - direccion_entrega
    - status: "confirmada"
      |
      v
  Registrar en SeguimientoEntrega (timeline)
      |
      v
  Incrementar total_pedidos del proveedor
      |
      v
  Auto-consumo presupuestal:
    - Buscar presupuesto activo del usuario
    - Sumar al gastado_total
    - Recalcular porcentaje_consumido
      |
      v
  Necesita aprobacion? --SI--> Flujo de aprobacion (seccion 3)
      |NO
      v
  Notificar al usuario: "Pedido confirmado con [proveedor]!"
  Limpiar historial de conversacion
```

### 4.2 Ciclo de Vida de la Orden

```
  confirmada --> preparando --> en_transito --> en_obra --> entregada
                                                   |
                                                   +--> con_incidencia --> entregada
  
  (Cualquier estado) --> cancelada
```

**Transiciones validas:**

| Desde | Hacia |
|-------|-------|
| confirmada | preparando, cancelada |
| preparando | en_transito, cancelada |
| en_transito | en_obra, cancelada |
| en_obra | entregada, con_incidencia, cancelada |
| con_incidencia | entregada, cancelada |

**Timestamps registrados por etapa:**
- `confirmada_at`, `preparando_at`, `en_transito_at`, `en_obra_at`, `entregada_at`, `cancelada_at`

**Datos de transporte (al pasar a en_transito):**
- `nombre_chofer`
- `telefono_chofer`
- `placas_vehiculo`
- `tipo_vehiculo`

**Al entregarse:**
- Se calcula `tiempo_entrega_minutos` (desde en_transito hasta entregada)
- Se incrementa `pedidos_cumplidos` del proveedor
- Se registra `fecha_entrega_real`

### 4.3 Tracking de Entrega (SeguimientoEntrega)

Cada cambio de status se registra en la tabla `SeguimientoEntrega`:
- `status_anterior`
- `status_nuevo`
- `origen` (usuario, admin, proveedor, agente)
- `nota` (contexto del cambio)
- `created_at` (timestamp)

Esto genera un timeline completo consultable via API.

### 4.4 Agente Proactivo -- Alertas Automaticas

El agente proactivo se ejecuta cada 10-15 minutos y realiza las siguientes acciones:

**1. Recordatorio de entrega proxima a proveedores**
- Condicion: orden en "confirmada" o "preparando" con fecha de entrega para hoy o manana
- Mensaje al proveedor con datos de la orden
- Pide responder PREPARANDO o PROBLEMA

**2. Alerta de recepcion a la obra**
- Condicion: orden cambio a "en_transito" en los ultimos 5 minutos
- Mensaje al usuario con datos del chofer, placas, vehiculo
- Pide responder RECIBIDO o PROBLEMA

**3. Confirmacion de entrega (insistencia)**
- Condicion: orden en "en_obra" por mas de 2 horas sin confirmacion
- Se envia a las 2h y 6h
- No se insiste despues de 24 horas

**4. Recordatorio de compromiso a proveedor**
- Condicion: orden en "confirmada" por mas de 4 horas sin avanzar a "preparando"
- Se envia a las 4h y 12h
- No se insiste despues de 48 horas

**5. Solicitud de calificacion post-entrega**
- Condicion: orden entregada hace exactamente 24 horas
- Solo si el usuario no ha calificado aun
- Pide calificacion 1-5 estrellas

**6. Alerta de retraso de entrega**
- Condicion: fecha_entrega_prometida ya paso y la orden no esta entregada
- Se alerta a AMBAS partes (proveedor y comprador)
- Se envia a la 1h, 4h y 12h de retraso
- No se insiste despues de 72 horas

**7. Recordatorio de cotizaciones pendientes**
- Condicion: solicitud a proveedor con 15+ minutos sin respuesta
- Maximo 2 recordatorios por solicitud
- Se envia a los 15 y 25 minutos

### 4.5 Incidencias

**Tipos de incidencia:**

| Tipo | Descripcion | Severidad default |
|------|-------------|-------------------|
| `cantidad_incorrecta` | Llego menos material del pedido | media |
| `especificacion` | Llego material diferente al pedido | grave |
| `entrega_tarde` | No llego a la hora acordada | leve |
| `material_danado` | Material roto, mojado, golpeado | media |
| `no_llego` | El pedido nunca llego | grave |
| `cobro_diferente` | El precio cobrado no coincide con la cotizacion | media |
| `otro` | Cualquier otro problema | media |

**Auto-clasificacion desde texto:**

El sistema analiza el mensaje del usuario buscando palabras clave:
- "faltaron 5 metros" --> `cantidad_incorrecta`
- "no era lo que pedi" --> `especificacion`
- "llego 3 horas tarde" --> `entrega_tarde`
- "las varillas venian dobladas" --> `material_danado`
- "nunca llego" --> `no_llego`
- "me cobraron de mas" --> `cobro_diferente`

Intensificadores de severidad: "nunca", "jamas", "todo mal", "inaceptable", "pesimo" --> severidad "grave"

**Extraccion inteligente de cantidades:**

El sistema intenta extraer datos numericos del texto:
- "pedi 15 metros y llegaron 12" --> esperado: 15, recibido: 12, unidad: m3
- "20 bultos y solo vinieron 18" --> esperado: 20, recibido: 18, unidad: bultos

**Flujo de resolucion:**

```
Incidencia creada (status: "abierta")
      |
      v
  Orden pasa a status "con_incidencia"
      |
      v
  Notificacion al usuario confirmando registro
      |
      v
  Admin resuelve: resolver_incidencia(id, resolucion)
      |
      v
  Status: "resuelta" + fecha_resolucion
```

---

## 5. Sistema de Pagos (Stripe)

### 5.1 Desglose de Montos

```
  Subtotal (precio del proveedor)     $18,500.00
  + Comision ObraYa (2%)              +   $370.00
  ----------------------------------------
  Total cobrado al cliente            $18,870.00
  
  Monto que recibe el proveedor:      $18,500.00
  Comision ObraYa:                       $370.00
```

### 5.2 Flujo de Pago

```
  1. Crear sesion Stripe Checkout
     - line_item: "ObraYa - Orden #42"
     - monto: total + 2% comision (en centavos MXN)
     - metadata: orden_id, subtotal, comision
     |
     v
  2. Redirigir al cliente a Stripe (URL de checkout)
     |
     v
  3. Cliente paga con tarjeta en Stripe
     |
     v
  4. Stripe redirige a /pagos/exito?session_id=xxx
     |
     v
  5. confirmar_pago():
     - Recuperar sesion de Stripe
     - Marcar orden como pagada
     - Registrar: metodo_pago, stripe_payment_id, fecha_pago
     - Registrar: comision_obraya, monto_proveedor
     - pago_proveedor_status = "pendiente"
     - Actualizar credit scoring del usuario
     |
     v
  6. Pago al proveedor (manual/SPEI):
     - registrar_pago_proveedor()
     - pago_proveedor_status = "pagado"
```

### 5.3 Simulacion (Testing)

Endpoint `simular_pago(orden_id)` que:
- Marca la orden como pagada sin pasar por Stripe
- metodo_pago = "simulado"
- stripe_payment_id = "sim_{orden_id}_{timestamp}"
- Ejecuta la misma logica de credit scoring

---

## 6. Presupuestos de Obra

### 6.1 Creacion de Presupuesto

```
crear_presupuesto(
    nombre_obra="Torre Norte Fase 2",
    direccion="Av. Patria 1234, Zapopan",
    fecha_inicio=...,
    fecha_fin_estimada=...,
    partidas=[
        {
            "nombre_material": "Concreto fc 250",
            "categoria": "concreto",
            "unidad": "m3",
            "cantidad_presupuestada": 500,
            "precio_unitario_estimado": 1200,
            "catalogo_id": 1
        },
        ...
    ]
)
```

Cada partida tiene:
- Nombre del material y categoria
- Unidad de medida
- Cantidad presupuestada y precio unitario estimado
- Monto presupuestado (cantidad x precio)
- Campos de tracking: cantidad_consumida, monto_gastado, porcentaje_consumido
- Flags de alerta: alerta_50_enviada, alerta_80_enviada, alerta_100_enviada
- Flag de bloqueo: bloqueado (true/false)

### 6.2 Tracking de Consumo

**Registro automatico al comprar:**

Al crear una orden, el sistema automaticamente:
1. Busca el presupuesto activo del usuario
2. Suma el total de la orden al `gastado_total`
3. Recalcula `porcentaje_consumido`

**Registro manual por partida:**

`registrar_consumo()` actualiza una partida especifica:
- Incrementa cantidad_consumida y monto_gastado
- Recalcula porcentaje de la partida
- Recalcula totales del presupuesto
- Dispara verificacion de alertas

### 6.3 Alertas por WhatsApp

```
  Consumo al 50%:
    "Tu partida de concreto para Torre Norte ya lleva el 50%
    consumido (250/500 m3). Vas bien, pero toma nota."

  Consumo al 80%:
    "*ALERTA:* Tu partida de concreto ya va al 80%.
    Solo te quedan 100 m3 del presupuesto."

  Consumo al 100%:
    "*PRESUPUESTO AGOTADO:* La partida de concreto llego al 100%.
    Se bloqueo la compra de este material.
    Contacta a tu administrador para ampliar el presupuesto."
```

Al 100% la partida se bloquea automaticamente. Se puede desbloquear manualmente por un admin.

### 6.4 Verificacion de Disponibilidad

Antes de cada compra, `verificar_disponibilidad()` revisa:
- Existe presupuesto activo con partida para ese material?
- La partida esta bloqueada?
- La cantidad solicitada excede lo restante?

Respuestas posibles:
- `permitido: True` --> la compra puede proceder
- `permitido: False, partida bloqueada` --> presupuesto agotado
- `permitido: False, excede disponible` --> la cantidad solicitada es mayor a lo restante
- Sin presupuesto --> compra libre (no hay restriccion)

---

## 7. Credit Scoring

### 7.1 Calculo del Score (0--100)

| Componente | Peso | Que mide |
|-----------|------|----------|
| Historial de pagos | 40% | Ratio pagos a tiempo vs tarde (<=7 dias = a tiempo) |
| Volumen de compras | 20% | Total gastado, normalizado a $500k MXN = 100% |
| Frecuencia | 15% | Pedidos completados, normalizado a 50 pedidos = 100% |
| Antiguedad | 10% | Dias desde registro, normalizado a 365 dias = 100% |
| Diversidad proveedores | 10% | Proveedores distintos usados, normalizado a 10 = 100% |
| Metodo de pago | 5% | Tarjeta=100, Transferencia=70, Efectivo=40 |

**Formula:**
```
Score = (pagos * 0.40) + (volumen * 0.20) + (frecuencia * 0.15)
      + (antiguedad * 0.10) + (diversidad * 0.10) + (metodo * 0.05)
```

### 7.2 Clasificacion

| Score | Nivel | Riesgo |
|-------|-------|--------|
| 85-100 | Excelente | Bajo |
| 70-84 | Bueno | Bajo |
| 50-69 | Regular | Medio |
| 0-49 | Malo | Alto |
| Sin pedidos | Sin historial | N/A |

### 7.3 Evaluacion de Credito

**Requisitos minimos para credito:**
- Al menos 5 pedidos completados
- Score >= 65

**Limite de credito sugerido:**
```
limite = score * total_gastado * 0.1 / 100
```
Ejemplo: score 80, $200,000 gastado --> limite = $16,000

**Actualizacion automatica:**

Cada vez que se confirma un pago:
1. Se actualiza `total_gastado` del usuario
2. Se incrementa `total_pedidos_completados`
3. Se calcula promedio movil de dias de pago
4. Se clasifica como pago a tiempo (<=7 dias) o tarde
5. Se recalcula el score completo

---

## 8. Calificacion de Proveedores

### 8.1 Calificacion Auto-calculada

Se ejecuta automaticamente al confirmar entrega de una orden.

| Eje | Peso | Como se calcula |
|-----|------|-----------------|
| Puntualidad | 35% | 5.0 base, -1 punto por cada 30 min de retraso |
| Cantidad correcta | 25% | 5.0 base, se reduce por ratio recibido/esperado |
| Especificacion correcta | 25% | 5.0 si correcto, 2.0 si incidencia de especificacion |
| Sin incidencias | 15% | 5.0 base, -1.5 por cada incidencia registrada |

**Resultado:** calificacion total ponderada de 1.0 a 5.0

### 8.2 Calificacion Manual

24 horas despues de la entrega, Nico pide calificacion al usuario:

```
Como calificas la experiencia? (1-5 estrellas)
1 - Muy mal
2 - Mal
3 - Regular
4 - Bien
5 - Excelente

Tambien puedes agregar un comentario despues del numero.
```

### 8.3 Impacto en el Sistema

Al registrar una calificacion se recalculan las metricas agregadas del proveedor (ultimas 50 ordenes):

- `calificacion`: promedio general (1.0-5.0)
- `tasa_puntualidad`: % de ordenes con puntualidad >= 4.0
- `tasa_cantidad_correcta`: % de ordenes con cantidad >= 4.5
- `tasa_especificacion_correcta`: % de ordenes con spec >= 4.5
- `total_incidencias`: conteo total de incidencias
- `total_ordenes_completadas`: conteo de ordenes entregadas

Estas metricas afectan directamente el orden de seleccion de proveedores en cotizacion activa.

---

## 9. Inteligencia de Precios

### 9.1 Registro de Precios

Cada cotizacion de proveedor se guarda automaticamente en `PrecioHistorico`:

| Campo | Descripcion |
|-------|-------------|
| `catalogo_id` | Producto normalizado del catalogo maestro |
| `producto_nombre` | Nombre original como lo dijo el proveedor |
| `producto_normalizado` | Nombre del catalogo maestro |
| `proveedor_id/nombre` | Quien cotizo |
| `precio_unitario` | Precio por unidad |
| `precio_efectivo` | Precio + flete prorrateado |
| `unidad` | m3, pieza, bulto, etc. |
| `cantidad_cotizada` | Volumen cotizado |
| `incluye_flete` | Si/No |
| `costo_flete` | Costo del flete (prorrateado) |
| `zona` | Zona geografica |
| `tiempo_entrega` | Compromiso de entrega |
| `fuente` | "cotizacion_activa", "manual", "referencia" |
| `fecha, dia_semana, mes, anio, trimestre` | Para analisis temporal |
| `es_outlier` | Flag de precio anomalo |
| `confianza` | Nivel de confianza del dato (0-1) |

### 9.2 Deteccion de Outliers

Un precio se marca como outlier si:
- Hay al menos 5 datos historicos para ese producto+unidad
- El precio es > 3x del promedio historico, o < 0.3x del promedio

Los outliers se excluyen del calculo de precio de referencia.

### 9.3 Precio de Referencia del Catalogo

El catalogo maestro mantiene un `precio_referencia` que se recalcula automaticamente:
- Se toman los ultimos 30 precios no-outlier
- Se calcula el promedio
- Se actualiza en el catalogo

### 9.4 Analytics Disponibles

- **Tendencia de precio:** precio promedio/min/max por mes, ultimos 6-12 meses
- **Variacion mensual:** cambio % mes a mes, deteccion de tendencia (alza/baja/estable)
- **Ranking de proveedores:** por precio promedio efectivo para un producto
- **Resumen de mercado:** total de datos, proveedores y productos trackeados, top 5 productos mas cotizados
- **Precio actual:** promedio de ultimas 10 cotizaciones no-outlier

---

## 10. Gestion de Equipos

### 10.1 Empresas

| Campo | Descripcion |
|-------|-------------|
| `nombre` | Razon social |
| `rfc` | RFC de la empresa |
| `direccion` | Direccion fiscal |
| `telefono` | Telefono de contacto |
| `email` | Email corporativo |
| `requiere_aprobacion` | Si las compras necesitan autorizacion |
| `limite_sin_aprobacion` | Monto maximo para compra directa sin autorizacion |
| `activo` | Si la empresa esta habilitada |

### 10.2 Miembros de Empresa

Cada miembro tiene:

| Campo | Descripcion |
|-------|-------------|
| `rol` | residente, superintendente, compras, director |
| `puede_pedir` | Puede solicitar materiales |
| `puede_aprobar` | Puede autorizar compras de otros |
| `puede_pagar` | Puede realizar pagos |
| `limite_aprobacion` | Monto maximo que puede aprobar (null = sin limite) |
| `activo` | Si el miembro esta habilitado |

### 10.3 Vendedores (Personal de Proveedores)

Cada proveedor puede tener multiples vendedores:

| Campo | Descripcion |
|-------|-------------|
| `nombre` | Nombre del vendedor |
| `telefono_whatsapp` | Su WhatsApp personal |
| `rol` | vendedor, gerente, mostrador, almacen |
| `solicitudes_atendidas` | Contador de solicitudes |
| `tiempo_respuesta_promedio` | En minutos |
| `calificacion` | Rating individual (1-5) |
| `disponible` | True/False (vacaciones, etc.) |
| `horario` | "L-V 8:00-18:00" |
| `categorias_especialidad` | JSON con categorias que domina |
| `activo` | Si esta habilitado |

**Routing inteligente:**

Al contactar un proveedor, el sistema busca el mejor vendedor:
1. Activo y disponible
2. Ordenado por tiempo_respuesta_promedio (mas rapido primero)
3. Si no hay vendedor disponible, usa el WhatsApp general del proveedor

---

## 11. Plataformas Web

### 11.1 Hub Central (`/hub/`)
Pagina principal con acceso a todos los modulos. Dashboard general del sistema.

### 11.2 Portal Clientes (`/portal/`)
Portal de autoservicio para compradores:
- Ver ordenes activas y completadas
- Timeline de seguimiento
- Historial de pedidos
- Calificaciones dadas

### 11.3 Portal Proveedores (`/portal/`)
Portal de autoservicio para proveedores:
- Solicitudes pendientes de cotizacion
- Ordenes en proceso
- Metricas de desempeno
- Calificaciones recibidas

### 11.4 Panel Admin (`/admin/`)
Panel de administracion del sistema:
- CRUD de proveedores, productos, usuarios
- Gestion de catalogo maestro
- Importacion de precios historicos
- Resolucion de incidencias

### 11.5 Dashboard Analytics (`/dashboard/`)
Metricas y graficas:
- Ordenes por status
- Ingresos y comisiones
- Proveedores mas usados
- Tiempos de respuesta

### 11.6 Simulador WhatsApp (`/sim/`)
Simulador web para probar el flujo de WhatsApp sin necesidad de un numero real. Permite:
- Enviar mensajes como comprador
- Enviar respuestas como proveedor
- Ver el flujo completo en tiempo real

### 11.7 Inteligencia de Precios (`/precios/`)
Panel de analisis de precios:
- Tendencias por producto
- Comparativa entre proveedores
- Deteccion de outliers
- Top productos mas cotizados

### 11.8 Presupuestos (`/presupuesto/`)
Gestion de presupuestos de obra:
- Crear/editar presupuestos con partidas
- Visualizar consumo por partida
- Alertas de porcentaje

### 11.9 Aprobaciones (`/aprobaciones/`)
Portal web para aprobar/rechazar ordenes:
- Lista de aprobaciones pendientes
- Detalle de cada solicitud
- Botones de aprobar/rechazar

### 11.10 Credit Scoring (`/credito/`)
Panel de credit scoring:
- Perfil crediticio de cada usuario
- Ranking de usuarios por score
- Evaluacion de elegibilidad

### 11.11 Pagos (`/pagos/`)
Modulo de pagos:
- Iniciar pago Stripe
- Simular pago (testing)
- Historial de pagos
- Pagos pendientes a proveedores

---

## 12. Integraciones Externas

| Servicio | Uso | Configuracion |
|----------|-----|---------------|
| **WhatsApp Cloud API (Meta)** | Canal principal de comunicacion con usuarios y proveedores | WHATSAPP_TOKEN, PHONE_NUMBER_ID, VERIFY_TOKEN |
| **WhatsApp via Twilio** | Fallback cuando Meta Cloud API no funciona | TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN |
| **Anthropic Claude** | Interpretacion de pedidos, parseo de respuestas de proveedores, clasificacion de incidencias | ANTHROPIC_API_KEY |
| **Groq Whisper** | Transcripcion de notas de voz a texto | GROQ_API_KEY |
| **Stripe** | Procesamiento de pagos con tarjeta, checkout | STRIPE_SECRET_KEY, STRIPE_PUBLISHABLE_KEY |
| **Nominatim/OpenStreetMap** | Conversion de coordenadas GPS a direcciones legibles | Sin API key (rate-limited) |
| **Google OAuth** | Autenticacion en portales web | GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET |

---

## 13. Cuentas Demo

### Empresa Demo

| Campo | Valor |
|-------|-------|
| Nombre | Constructora Demo SA de CV |
| RFC | CDM000101XXX |
| Direccion | Av. Patria 1234, Zapopan, Jalisco |
| Requiere aprobacion | Si |
| Limite sin aprobacion | $100,000 MXN |

### Usuarios Demo

| Telefono | Nombre | Rol | Puede pedir | Puede aprobar | Puede pagar | Limite |
|----------|--------|-----|------------|---------------|-------------|--------|
| 5200000001 | Admin Demo | Director | Si | Si | Si | Sin limite |
| 5200000002 | Residente Demo | Residente | Si | No | No | $50,000 |
| 5200000003 | Superintendente Demo | Superintendente | Si | Si | No | $150,000 |
| 5200000004 | Compras Demo | Compras | Si | Si | Si | $500,000 |

### Proveedores Demo

| Telefono WA | Nombre | Tipo | Municipio | Categorias | Calificacion |
|-------------|--------|------|-----------|------------|--------------|
| 5200000010 | Materiales Zapopan Demo | Mediano | Zapopan | acero, cemento, arena, grava, block | 4.2 |
| 5200000011 | Ferreteria GDL Demo | Pequeno | Guadalajara | ferreteria, plomeria, electricidad, pintura | 4.5 |
| 5200000012 | Concretos del Bajio Demo | Grande | Tlaquepaque | concreto, cemento, mortero, prefabricados | 3.8 |

### Como probar

1. **Simulador web:** Usar `/sim/` para enviar mensajes como cualquier usuario demo
2. **Flujo comprador:** Enviar mensaje desde telefono 5200000002 (Residente) pidiendo material
3. **Flujo proveedor:** Responder desde telefono 5200000010 con precios
4. **Flujo aprobacion:** Crear orden > $100,000 desde Residente --> Director recibe solicitud
5. **Pagos:** Usar endpoint de simulacion para probar sin Stripe real

---

## Anexo: Flujo Completo End-to-End

```
RESIDENTE                    NICO (IA)                   PROVEEDORES
    |                            |                            |
    |-- "Necesito 15m3 de       |                            |
    |   concreto fc250 para     |                            |
    |   manana en Zapopan" ---->|                            |
    |                            |                            |
    |                            |-- Interpretar con Claude   |
    |                            |-- Seleccionar 20 provs     |
    |                            |                            |
    |                            |-- "Hola, soy Nico..." --->|-- Proveedor A
    |                            |-- "Hola, soy Nico..." --->|-- Proveedor B
    |                            |-- "Hola, soy Nico..." --->|-- Proveedor C
    |                            |                            |
    |<-- "Estoy cotizando con   |                            |
    |    3 proveedores..."      |                            |
    |                            |                            |
    |                            |<-- "$16,500 con flete" ----|-- Proveedor A
    |<-- "1 proveedor respondio"|                            |
    |                            |                            |
    |                            |<-- "$18,200 sin flete" ----|-- Proveedor C
    |                            |                            |
    |                            |-- (15min sin resp.) ------>|-- Recordatorio a B
    |                            |                            |
    |<-- "Comparativa:          |                            |
    |    1. Zapopan $16,500     |                            |
    |    2. Bajio $19,700       |                            |
    |    Elige un numero" ------|                            |
    |                            |                            |
    |-- "1" ------------------->|                            |
    |                            |                            |
    |                            |-- Verificar aprobacion     |
    |                            |-- Crear orden              |
    |                            |-- Registrar presupuesto    |
    |                            |                            |
    |<-- "Pedido confirmado     |                            |
    |    con Materiales Zapopan |                            |
    |    Orden #42, $16,500" ---|                            |
    |                            |                            |
    |                   ... HORAS DESPUES ...                 |
    |                            |                            |
    |                            |-- Alerta entrega -------->|-- Proveedor A
    |<-- "Tu pedido va en       |                            |
    |    camino! Chofer: Juan   |                            |
    |    Placas: ABC-123" ------|                            |
    |                            |                            |
    |<-- "El camion ya llego.   |                            |
    |    Responde OK o          |                            |
    |    Problema" -------------|                            |
    |                            |                            |
    |-- "OK" ------------------>|                            |
    |                            |                            |
    |                            |-- Calcular calificacion    |
    |                            |-- Actualizar metricas      |
    |                            |-- Registrar precios hist.  |
    |                            |                            |
    |<-- "Entrega completada!   |                            |
    |    Calificacion: 4.7/5    |                            |
    |    Gracias por usar       |                            |
    |    ObraYa!" --------------|                            |
    |                            |                            |
    |                   ... 24 HORAS DESPUES ...              |
    |                            |                            |
    |<-- "Como calificas tu     |                            |
    |    pedido? (1-5)" --------|                            |
    |                            |                            |
    |-- "5 excelente servicio"->|                            |
    |                            |-- Registrar calificacion   |
    |                            |-- Recalcular metricas prov |
```

---

*Documento generado como referencia operativa del sistema ObraYa.*
*Ultima actualizacion: Abril 2026*

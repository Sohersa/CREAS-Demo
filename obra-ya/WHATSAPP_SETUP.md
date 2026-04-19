# WhatsApp — Configuracion y Troubleshooting

## 🚨 Token expirado (error 190/463)

Si ves en los logs:
```
TOKEN WHATSAPP EXPIRADO — renuevalo en Meta Business
```

o `/admin/api/whatsapp/health` retorna `"status": "token_expired"`, sigue estos pasos.

## Solucion rapida (2 minutos) — Token temporal

Util para desarrollo. Expira en 24 horas a 60 dias segun el tipo.

1. Ve a https://developers.facebook.com/apps
2. Selecciona tu app de ObraYa
3. Menu izquierdo: **WhatsApp > API Setup**
4. Seccion **Temporary access token** → copia el token
5. Pega en `.env`:
   ```
   WHATSAPP_TOKEN=EAAB...nuevo_token
   ```
6. Reinicia el servidor
7. Verifica: `curl http://localhost:8000/admin/api/whatsapp/health`

## Solucion permanente — System User token (RECOMENDADO para produccion)

Un System User tiene un token que **NO expira nunca**. Hazlo una vez y olvidate.

### Pasos

1. **Crear System User**
   - Entra a https://business.facebook.com
   - **Settings** (engranaje abajo izquierda) → **System Users**
   - Click **Add** → dale un nombre tipo `ObraYa Backend`
   - Rol: **Admin**
   - Click **Create system user**

2. **Asignar assets** (permisos a tu app y numero de WhatsApp)
   - Con el System User seleccionado, click **Add Assets**
   - Elige **Apps** → marca tu app de ObraYa → permisos: **Manage app**
   - Click **Add Assets** otra vez → **WhatsApp Accounts** → marca tu WABA → **Full control**

3. **Generar token permanente**
   - Con el System User seleccionado, click **Generate New Token**
   - Selecciona tu app
   - Expiracion: **Never**
   - Permisos requeridos:
     - `whatsapp_business_messaging` (enviar mensajes)
     - `whatsapp_business_management` (listar templates, numeros)
     - `business_management` (acceso general)
   - Click **Generate Token**
   - **COPIA EL TOKEN** (no se muestra de nuevo)

4. **Pega en `.env`**
   ```
   WHATSAPP_TOKEN=EAAB...token_permanente
   ```

5. **Guarda el backup**
   - Guarda el token en un password manager (1Password, Bitwarden)
   - Documenta cuando fue creado

6. **Reinicia y valida**
   ```bash
   curl http://localhost:8000/admin/api/whatsapp/health
   ```
   Debe retornar `"status": "healthy"`.

## Troubleshooting — otros errores

### `phone_id_invalid`
El `WHATSAPP_PHONE_ID` en `.env` no existe. Vuelve a copiarlo desde Meta Business → WhatsApp → API Setup (es el numero largo junto al telefono).

### `recipient_not_allowed` (error 131026)
El numero destino no esta en la lista de testers. En modo desarrollo, Meta solo permite enviar a numeros registrados como testers.
- Entra a la app en developers.facebook.com
- **WhatsApp > API Setup > To**
- Agrega el numero

### `requires_template` (error 131047)
Estas fuera de la ventana de 24 horas — no puedes iniciar conversacion con texto libre.
Debes usar una plantilla aprobada. Ver `enviar_mensaje_template()` en `app/services/whatsapp.py`.

Para aprobar una plantilla:
- Meta Business Manager → WhatsApp Manager → **Message Templates**
- **Create Template** → sigue el flujo (categoria, idioma es_MX, componentes)
- Espera aprobacion (usualmente < 24h)

### `rate_limit`
Meta tiene limites por segundo/dia. Reduce la frecuencia de envios o usa un numero con tier mas alto.

## Health check endpoints

| Endpoint | Descripcion |
|----------|-------------|
| `GET /health` | Status global (incluye whatsapp) |
| `GET /admin/api/whatsapp/health` | Diagnostico detallado de WhatsApp con sugerencia |
| `GET /admin/api/diagnostico` | Que variables estan configuradas (sin exponer secretos) |

## Monitoreo proactivo

Agrega el endpoint `/admin/api/whatsapp/health` a tu uptime bot (UptimeRobot, Better Uptime).
Cuando el status deje de ser `healthy`, recibes alerta.

Ejemplo con curl que te avisa:
```bash
curl -s http://tu-servidor.com/admin/api/whatsapp/health | jq -r 'if .ok then "OK" else .mensaje end'
```

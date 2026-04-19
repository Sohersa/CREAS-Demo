# ObraYa Design System

El sistema de diseno oficial vive en `static/design/` — bundle completo
exportado desde Claude Design.

## Archivos clave

| Archivo | Proposito |
|---------|-----------|
| `static/design/Landing.html` | Landing publica, servida en `/` y `/landing` |
| `static/design/Playground.html` | Visualizador del proceso, servido en `/playground` |
| `static/design/design/tokens.css` | **Variables CSS base** — colores, typography, spacing, motion |
| `static/design/design/components.css` | Componentes visuales (cards, buttons, maps, etc.) |
| `static/design/design/playground.css` | Estilos especificos del Playground |
| `static/design/design/*.jsx` | Componentes React (Icon, WhatsAppConversation, InteractiveCockpit, CapMap, ProcessMovie, etc.) |

## Design tokens resumen

**Colores base (Stripe-inspired, fondo blanco):**
- `--paper`: `#FFFFFF` (fondo principal)
- `--paper-2`: `#F6F9FC` (fondo secundario)
- `--ink`: `#0A2540` (texto principal — azul marino)
- `--ink-dim`: `#697386`
- `--ink-muted`: `#8792A2`

**Acentos:**
- `--violet`: `#635BFF` (Stripe purple — accent principal)
- `--orange`: `#FF7A45` (ObraYa brand orange)
- `--cyan`: `#00D4FF`
- `--whatsapp`: `#25D366`

**Typography:**
- `--font-sans`: `'Inter Tight'`
- `--font-mono`: `'JetBrains Mono'`
- letter-spacing: `-0.011em`

**Variants via data attributes:**
```html
<html data-accent="violet" data-motion="default">
<html data-accent="orange">  <!-- cambia el color acento -->
<html data-motion="calm">    <!-- reduce animaciones -->
<html data-motion="off">     <!-- sin animaciones -->
```

## Paginas actualmente usando el design system

- `GET /` — Landing principal (file response al bundle)
- `GET /landing` — alias de `/`
- `GET /playground` — visualizador del proceso end-to-end

## Paginas pendientes de migrar

Las siguientes paginas tienen estilos inline propios (dark theme) que hay
que re-skinear para coincidir con el design system. En cada una hay que:

1. Importar tokens.css + components.css
2. Remover el `<style>` inline local
3. Reemplazar las clases propias por las del design system
4. Agregar `data-accent="violet"` al `<html>`

| Pagina | Archivo | Prioridad |
|--------|---------|-----------|
| Portal cliente/proveedor | `app/routers/portal.py` | Alta — es la pagina mas visitada |
| Admin general | `app/routers/admin.py` | Alta |
| Dashboard pagos | `app/routers/pagos.py` | Media |
| Simulador | `app/routers/simulador.py` | Baja |
| Hub | `app/routers/hub.py` | Alta |
| Presupuesto | `app/routers/presupuesto.py` | Media |
| Landing antiguo (inline) | `app/routers/landing.py` | Ya reemplazado |
| WhatsApp admin | `app/routers/admin.py` (`whatsapp_admin_page`) | Media |

## Como migrar una pagina

### Ejemplo: pagina HTML inline
```python
# ANTES
@router.get("/foo", response_class=HTMLResponse)
def mi_pagina():
    return HTMLResponse("""
    <html>
    <head><style>body { background: #0a0a0a; }</style></head>
    <body>...</body>
    </html>
    """)

# DESPUES
@router.get("/foo", response_class=HTMLResponse)
def mi_pagina():
    return HTMLResponse("""
    <html data-accent="violet">
    <head>
      <link rel="stylesheet" href="/static/design/design/tokens.css">
      <link rel="stylesheet" href="/static/design/design/components.css">
    </head>
    <body>
      <!-- usa variables CSS del design system -->
      <div style="background: var(--paper); color: var(--ink);">...</div>
    </body>
    </html>
    """)
```

### Clases utiles de `components.css`

(Lista abreviada — ver archivo completo para todas)

- `.card` — card base blanco
- `.btn-primary` — boton violeta
- `.pill` — pildora de status
- `.capmap2-*` — capability map interactivo
- `.whatsapp-*` — render de conversacion WhatsApp
- `.mini-whatsapp-*` — mockup de telefono pequeno

## Componentes React (JSX)

Los componentes en `design/*.jsx` se cargan via Babel standalone en
Landing.html y Playground.html. Se pueden reusar en cualquier pagina que
necesite visualizaciones complejas (maps, cockpit, conversations).

Si se quieren usar en la app Python, pueden:
1. Servirse como pagina estatica igual que Landing/Playground
2. O portarse a plantillas Jinja si quieres renderizado server-side

## Siguientes pasos

Para completar la migracion del design system:

1. **Portal** — re-templatizar `app/routers/portal.py` para usar tokens
2. **Admin** — idem `app/routers/admin.py`
3. **Hub** — idem `app/routers/hub.py`
4. Considerar extraer los HTML inline a `templates/*.html` con Jinja2
5. Extraer los SVG de componentes a `static/img/` para reuso

## Referencia

El bundle viene de `claude.ai/design` y fue exportado desde un proyecto
colaborativo donde se diseno todo el flujo end-to-end de ObraYa.

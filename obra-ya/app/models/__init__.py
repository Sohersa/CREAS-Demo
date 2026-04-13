"""
Importar todos los modelos para que SQLAlchemy los registre.
"""
from app.models.catalogo import CatalogoMaestro, AliasProducto
from app.models.proveedor import Proveedor
from app.models.producto import Producto
from app.models.usuario import Usuario
from app.models.pedido import Pedido
from app.models.cotizacion import Cotizacion, Comparativa
from app.models.orden import Orden
from app.models.seguimiento import SeguimientoEntrega
from app.models.incidencia import IncidenciaEntrega
from app.models.calificacion import CalificacionProveedor
from app.models.solicitud_proveedor import SolicitudProveedor
from app.models.precio_historico import PrecioHistorico
from app.models.empresa import Empresa
from app.models.miembro_empresa import MiembroEmpresa
from app.models.aprobacion import Aprobacion
from app.models.presupuesto import PresupuestoObra, PartidaPresupuesto
from app.models.mensaje_historico import MensajeHistorico
from app.models.vendedor import Vendedor

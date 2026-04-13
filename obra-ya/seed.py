"""
Script para cargar datos semilla en la base de datos.
Carga: Catalogo Maestro → Aliases → Proveedores → Productos (vinculados al catalogo)

Ejecutar: python seed.py
"""
import json
import sys
import os

# Agregar el directorio raiz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, SessionLocal, crear_tablas
from app.models.catalogo import CatalogoMaestro, AliasProducto
from app.models.proveedor import Proveedor
from app.models.producto import Producto


def limpiar_bd(db):
    """Limpia todas las tablas en orden correcto (por foreign keys)."""
    db.query(AliasProducto).delete()
    db.query(Producto).delete()
    db.query(CatalogoMaestro).delete()
    db.query(Proveedor).delete()
    db.commit()


def cargar_catalogo_maestro(db):
    """Carga los 30 productos maestros y sus aliases."""
    ruta = os.path.join(os.path.dirname(__file__), "data", "catalogo_maestro.json")
    with open(ruta, "r", encoding="utf-8") as f:
        data = json.load(f)

    productos_maestros = 0
    aliases_creados = 0

    for item in data["catalogo"]:
        maestro = CatalogoMaestro(
            nombre=item["nombre"],
            categoria=item["categoria"],
            subcategoria=item.get("subcategoria"),
            unidad=item["unidad"],
            descripcion=item.get("descripcion", ""),
            precio_referencia=item.get("precio_referencia"),
            activo=True,
        )
        db.add(maestro)
        db.flush()
        productos_maestros += 1

        # Agregar el nombre oficial como primer alias
        alias_oficial = AliasProducto(
            catalogo_id=maestro.id,
            alias=item["nombre"].lower(),
            fuente="manual",
            confianza=1.0,
            activo=True,
        )
        db.add(alias_oficial)
        aliases_creados += 1

        # Agregar todos los aliases
        for alias_text in item.get("aliases", []):
            alias = AliasProducto(
                catalogo_id=maestro.id,
                alias=alias_text.lower().strip(),
                fuente="manual",
                confianza=1.0,
                activo=True,
            )
            db.add(alias)
            aliases_creados += 1

    db.commit()
    print(f"  Catalogo Maestro: {productos_maestros} productos")
    print(f"  Aliases: {aliases_creados} nombres alternativos")
    return productos_maestros, aliases_creados


def encontrar_catalogo_id(db, nombre_producto):
    """
    Busca en aliases para encontrar el catalogo_id de un producto.
    Esto vincula el nombre del proveedor con el producto maestro.
    """
    nombre_lower = nombre_producto.lower().strip()

    # Busqueda exacta primero
    alias = db.query(AliasProducto).filter(
        AliasProducto.alias == nombre_lower,
        AliasProducto.activo == True,
    ).first()
    if alias:
        return alias.catalogo_id

    # Busqueda parcial (el nombre del proveedor contiene el alias o viceversa)
    aliases = db.query(AliasProducto).filter(AliasProducto.activo == True).all()
    mejor_match = None
    mejor_longitud = 0

    for a in aliases:
        if a.alias in nombre_lower or nombre_lower in a.alias:
            if len(a.alias) > mejor_longitud:
                mejor_match = a
                mejor_longitud = len(a.alias)

    if mejor_match:
        return mejor_match.catalogo_id

    return None


def cargar_proveedores(db):
    """Carga proveedores y vincula sus productos al catalogo maestro."""
    ruta = os.path.join(os.path.dirname(__file__), "data", "proveedores_seed.json")
    with open(ruta, "r", encoding="utf-8") as f:
        data = json.load(f)

    proveedores_creados = 0
    productos_creados = 0
    productos_vinculados = 0

    for prov_data in data["proveedores"]:
        proveedor = Proveedor(
            nombre=prov_data["nombre"],
            tipo=prov_data["tipo"],
            municipio=prov_data["municipio"],
            telefono_whatsapp=prov_data.get("telefono_whatsapp", ""),
            categorias=json.dumps(prov_data["categorias"]),
            metodo_contacto=prov_data.get("metodo_contacto", "whatsapp"),
            calificacion=prov_data.get("calificacion", 4.0),
            total_pedidos=prov_data.get("total_pedidos", 0),
            pedidos_cumplidos=prov_data.get("pedidos_cumplidos", 0),
            activo=True,
        )
        db.add(proveedor)
        db.flush()
        proveedores_creados += 1

        for prod_data in prov_data.get("productos", []):
            # Buscar catalogo_id por el nombre del producto
            catalogo_id = encontrar_catalogo_id(db, prod_data["nombre"])

            producto = Producto(
                proveedor_id=proveedor.id,
                catalogo_id=catalogo_id,
                categoria=prod_data["categoria"],
                nombre=prod_data["nombre"],
                nombre_proveedor=prod_data["nombre"],  # Guardar nombre original
                unidad=prod_data["unidad"],
                precio_unitario=prod_data["precio_unitario"],
                disponibilidad=prod_data.get("disponibilidad", "inmediata"),
                activo=True,
            )
            db.add(producto)
            productos_creados += 1

            if catalogo_id:
                productos_vinculados += 1

                # Agregar el nombre del proveedor como alias nuevo (si no existe)
                nombre_lower = prod_data["nombre"].lower().strip()
                existe = db.query(AliasProducto).filter(
                    AliasProducto.alias == nombre_lower,
                    AliasProducto.catalogo_id == catalogo_id,
                ).first()

                if not existe:
                    nuevo_alias = AliasProducto(
                        catalogo_id=catalogo_id,
                        alias=nombre_lower,
                        fuente="proveedor",
                        proveedor_id=proveedor.id,
                        confianza=1.0,
                        activo=True,
                    )
                    db.add(nuevo_alias)

        vinc_text = f", {sum(1 for p in prov_data.get('productos', []) if encontrar_catalogo_id(db, p['nombre']))} vinculados"
        print(f"  + {proveedor.nombre} ({len(prov_data.get('productos', []))} productos{vinc_text})")

    db.commit()
    print(f"\n  Proveedores: {proveedores_creados}")
    print(f"  Productos: {productos_creados} ({productos_vinculados} vinculados al catalogo)")

    if productos_creados > productos_vinculados:
        no_vinculados = productos_creados - productos_vinculados
        print(f"  ⚠️  {no_vinculados} productos NO se pudieron vincular automaticamente")


def cargar_semilla():
    """Carga todo en orden: catalogo → proveedores → productos."""
    crear_tablas()

    db = SessionLocal()

    # Verificar si ya hay datos
    count = db.query(Proveedor).count()
    if count > 0:
        print(f"Ya hay {count} proveedores. Limpiando para recargar...")
        limpiar_bd(db)

    print("\n--- Paso 1: Catalogo Maestro + Aliases ---")
    cargar_catalogo_maestro(db)

    print("\n--- Paso 2: Proveedores + Productos ---")
    cargar_proveedores(db)

    # Resumen final
    total_maestro = db.query(CatalogoMaestro).count()
    total_aliases = db.query(AliasProducto).count()
    total_proveedores = db.query(Proveedor).count()
    total_productos = db.query(Producto).count()
    total_vinculados = db.query(Producto).filter(Producto.catalogo_id.isnot(None)).count()

    print(f"\n{'='*50}")
    print(f"SEMILLA COMPLETA:")
    print(f"  Catalogo Maestro: {total_maestro} productos estandar")
    print(f"  Aliases: {total_aliases} nombres alternativos")
    print(f"  Proveedores: {total_proveedores}")
    print(f"  Productos: {total_productos} ({total_vinculados} vinculados)")
    print(f"{'='*50}")

    db.close()


if __name__ == "__main__":
    print("Cargando datos semilla de ObraYa...")
    print("=" * 50)
    cargar_semilla()

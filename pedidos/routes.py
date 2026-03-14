from flask import Blueprint, render_template, request, redirect, url_for, flash
from forms import PedidoForm, BusquedaForm
from models import db, Cliente, Pedido, DetallePedido, Pizza

pedidos_bp = Blueprint('pedidos_bp', __name__)

PRECIOS_TAMANO = {'Chica': 40, 'Mediana': 80, 'Grande': 120}
PRECIO_INGREDIENTE = 10

@pedidos_bp.route("/", methods=['GET', 'POST'])
@pedidos_bp.route("/index", methods=['GET', 'POST'])
def index():
    form = PedidoForm()
    
    # Buscamos si hay un pedido "En Proceso" (donde el total sea 0 o esté abierto)
    # Para fines del examen, buscaremos el último pedido del día que no se ha "Cerrado"
    pedido_actual = Pedido.query.filter_by(total=0).order_by(Pedido.id_pedido.desc()).first()
    
    carrito = []
    cliente_obj = None

    if pedido_actual:
        cliente_obj = Cliente.query.get(pedido_actual.id_cliente)
        # Llenamos el carrito desde la BD
        detalles_db = db.session.query(DetallePedido, Pizza).join(Pizza).filter(DetallePedido.id_pedido == pedido_actual.id_pedido).all()
        for det, piz in detalles_db:
            carrito.append({
                'id_detalle': det.id_detalle, # Para poder quitarlo después
                'tamano': piz.tamano,
                'ingredientes': piz.ingredientes,
                'num_pizzas': det.cantidad,
                'subtotal': det.subtotal
            })

    if request.method == 'POST' and form.validate_on_submit():
        # 1. Si no hay pedido actual, creamos cliente y pedido
        if not pedido_actual:
            d, m, a = form.fecha.data.split('-')
            fecha_db = f"{a}-{m}-{d}"
            
            nuevo_cliente = Cliente(nombre=form.nombre.data, direccion=form.direccion.data, telefono=form.telefono.data)
            db.session.add(nuevo_cliente)
            db.session.commit()
            
            pedido_actual = Pedido(id_cliente=nuevo_cliente.id_cliente, fecha=fecha_db, total=0)
            db.session.add(pedido_actual)
            db.session.commit()

        # 2. Calculamos y guardamos la pizza
        costo_base = PRECIOS_TAMANO.get(form.tamano.data, 0)
        costo_ing = len(form.ingredientes.data) * PRECIO_INGREDIENTE
        sub_total = (costo_base + costo_ing) * form.num_pizzas.data

        nueva_p = Pizza(
            tamano=form.tamano.data, 
            ingredientes=", ".join(form.ingredientes.data) if form.ingredientes.data else "Queso",
            precio=(costo_base + costo_ing)
        )
        db.session.add(nueva_p)
        db.session.commit()

        # 3. Guardamos el detalle vinculado al pedido
        nuevo_det = DetallePedido(
            id_pedido=pedido_actual.id_pedido,
            id_pizza=nueva_p.id_pizza,
            cantidad=form.num_pizzas.data,
            subtotal=sub_total
        )
        db.session.add(nuevo_det)
        db.session.commit()

        return redirect(url_for('pedidos_bp.index'))

    # Si hay un pedido activo, autocompletamos los datos del cliente en el form
    if cliente_obj:
        form.nombre.data = cliente_obj.nombre
        form.direccion.data = cliente_obj.direccion
        form.telefono.data = cliente_obj.telefono
        # Nota: La fecha se queda como la pusiste al inicio

    return render_template("index.html", form=form, carrito=carrito)

@pedidos_bp.route("/quitar/<int:id_detalle>", methods=['POST'])
def quitar(id_detalle):
    detalle = DetallePedido.query.get(id_detalle)
    if detalle:
        # Borramos el detalle y la pizza asociada para no dejar basura
        pizza = Pizza.query.get(detalle.id_pizza)
        db.session.delete(detalle)
        db.session.delete(pizza)
        db.session.commit()
    return redirect(url_for('pedidos_bp.index'))

@pedidos_bp.route("/terminar", methods=['POST'])
def terminar():
    pedido_actual = Pedido.query.filter_by(total=0).order_by(Pedido.id_pedido.desc()).first()
    
    if pedido_actual:
        # Calculamos el total real de todos sus detalles
        total_final = db.session.query(db.func.sum(DetallePedido.subtotal)).filter(DetallePedido.id_pedido == pedido_actual.id_pedido).scalar()
        
        if total_final:
            pedido_actual.total = total_final
            db.session.commit()
            flash(f"¡Venta registrada con éxito! Total: ${total_final}", "success")
        else:
            flash("No puedes terminar un pedido vacío.", "error")
    
    return redirect(url_for('pedidos_bp.index'))

# Rutas de ventas y detalle se quedan igual (esas no usan session)
@pedidos_bp.route("/ventas", methods=['GET', 'POST'])
def ventas():
    form = BusquedaForm()
    resultados = []; total_acumulado = 0
    if request.method == 'POST' and form.validate_on_submit():
        tipo, valor = form.tipo_busqueda.data, form.valor.data.lower().strip()
        meses = {'enero':1,'febrero':2,'marzo':3,'abril':4,'mayo':5,'junio':6,'julio':7,'agosto':8,'septiembre':9,'octubre':10,'noviembre':11,'diciembre':12}
        dias = {'lunes':0,'martes':1,'miercoles':2,'jueves':3,'viernes':4,'sabado':5,'domingo':6}
        pedidos_all = db.session.query(Pedido, Cliente).join(Cliente).filter(Pedido.total > 0).all()
        for p, c in pedidos_all:
            match = False
            if tipo == 'dia' and valor in dias and p.fecha.weekday() == dias[valor]: match = True
            elif tipo == 'mes' and valor in meses and p.fecha.month == meses[valor]: match = True
            if match:
                resultados.append({'id_pedido': p.id_pedido, 'cliente': c.nombre, 'fecha': p.fecha, 'total': p.total})
                total_acumulado += p.total
    return render_template("ventas.html", form=form, resultados=resultados, total_ventas=total_acumulado)

@pedidos_bp.route("/detalle/<int:id_pedido>")
def detalle(id_pedido):
    pedido = Pedido.query.get_or_404(id_pedido)
    cliente = Cliente.query.get(pedido.id_cliente)
    detalles = db.session.query(DetallePedido, Pizza).join(Pizza).filter(DetallePedido.id_pedido == id_pedido).all()
    return render_template("detalle.html", pedido=pedido, cliente=cliente, detalles=detalles)
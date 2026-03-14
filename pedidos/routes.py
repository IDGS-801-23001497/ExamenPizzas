from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from forms import PedidoForm, BusquedaForm
from models import db, Cliente, Pedido, DetallePedido, Pizza

pedidos_bp = Blueprint('pedidos_bp', __name__)

PRECIOS_TAMANO = {'Chica': 40, 'Mediana': 80, 'Grande': 120}
PRECIO_INGREDIENTE = 10

@pedidos_bp.route("/", methods=['GET', 'POST'])
@pedidos_bp.route("/index", methods=['GET', 'POST'])
def index():
    form = PedidoForm()
    if 'carrito' not in session:
        session['carrito'] = []
    if request.method == 'GET' and 'cliente' in session:
        form.nombre.data = session['cliente']['nombre']
        form.direccion.data = session['cliente']['direccion']
        form.telefono.data = session['cliente']['telefono']
        form.fecha.data = session['cliente']['fecha']

    if request.method == 'POST' and form.validate_on_submit():
        session['cliente'] = {
            'nombre': form.nombre.data,
            'direccion': form.direccion.data,
            'telefono': form.telefono.data,
            'fecha': form.fecha.data
        }
        tamano = form.tamano.data
        ingredientes = form.ingredientes.data
        num_pizzas = form.num_pizzas.data
        
        costo_base = PRECIOS_TAMANO.get(tamano, 0)
        costo_ingredientes = len(ingredientes) * PRECIO_INGREDIENTE
        subtotal = (costo_base + costo_ingredientes) * num_pizzas
        carrito_temp = session['carrito']
        carrito_temp.append({
            'tamano': tamano,
            'ingredientes': ", ".join(ingredientes) if ingredientes else "Queso",
            'num_pizzas': num_pizzas,
            'subtotal': subtotal
        })
        session['carrito'] = carrito_temp
        session.modified = True 

        return redirect(url_for('pedidos_bp.index'))

    return render_template("index.html", form=form, carrito=session['carrito'])

@pedidos_bp.route("/quitar/<int:id_fila>", methods=['POST'])
def quitar(id_fila):
    if 'carrito' in session:
        carrito = session['carrito']
        if 0 <= id_fila < len(carrito):
            carrito.pop(id_fila)
            session['carrito'] = carrito
            session.modified = True
    return redirect(url_for('pedidos_bp.index'))

@pedidos_bp.route("/terminar", methods=['POST'])
def terminar():
    carrito = session.get('carrito', [])
    cliente_data = session.get('cliente')

    if not carrito or not cliente_data:
        flash("No hay datos para procesar el pedido.", "error")
        return redirect(url_for('pedidos_bp.index'))

    total_pedido = sum(p['subtotal'] for p in carrito)
    try:
        d, m, a = cliente_data['fecha'].split('-')
        fecha_db = f"{a}-{m}-{d}"
    except:
        fecha_db = "2026-03-13"

    nuevo_cliente = Cliente(
        nombre=cliente_data['nombre'], 
        direccion=cliente_data['direccion'], 
        telefono=cliente_data['telefono']
    )
    db.session.add(nuevo_cliente)
    db.session.commit()
    nuevo_pedido = Pedido(
        id_cliente=nuevo_cliente.id_cliente, 
        fecha=fecha_db, 
        total=total_pedido
    )
    db.session.add(nuevo_pedido)
    db.session.commit()
    for item in carrito:
        nueva_p = Pizza(
            tamano=item['tamano'], 
            ingredientes=item['ingredientes'], 
            precio=item['subtotal']/item['num_pizzas']
        )
        db.session.add(nueva_p)
        db.session.commit()
        db.session.add(DetallePedido(
            id_pedido=nuevo_pedido.id_pedido, 
            id_pizza=nueva_p.id_pizza, 
            cantidad=item['num_pizzas'], 
            subtotal=item['subtotal']
        ))
    db.session.commit()
    flash(f"¡Venta de {cliente_data['nombre']} registrada! Total: ${total_pedido}", "success")
    session.pop('carrito', None)
    session.pop('cliente', None)
    return redirect(url_for('pedidos_bp.index'))

@pedidos_bp.route("/ventas", methods=['GET', 'POST'])
def ventas():
    form = BusquedaForm()
    resultados = []
    total_acumulado = 0
    
    if request.method == 'POST' and form.validate_on_submit():
        tipo = form.tipo_busqueda.data
        valor = form.valor.data.lower().strip()
        meses = {'enero':1,'febrero':2,'marzo':3,'abril':4,'mayo':5,'junio':6,'julio':7,'agosto':8,'septiembre':9,'octubre':10,'noviembre':11,'diciembre':12}
        dias = {'lunes':0,'martes':1,'miercoles':2,'jueves':3,'viernes':4,'sabado':5,'domingo':6}
        pedidos_all = db.session.query(Pedido, Cliente).join(Cliente).all()
        for p, c in pedidos_all:
            match = False
            if tipo == 'dia' and valor in dias and p.fecha.weekday() == dias[valor]:
                match = True
            elif tipo == 'mes' and valor in meses and p.fecha.month == meses[valor]:
                match = True
            
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
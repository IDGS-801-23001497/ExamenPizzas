from flask_sqlalchemy import SQLAlchemy
import datetime

db = SQLAlchemy()

# 1. Modelo de Pizzas
class Pizza(db.Model):
    __tablename__ = 'pizzas'
    id_pizza = db.Column(db.Integer, primary_key=True)
    tamano = db.Column(db.String(20))
    ingredientes = db.Column(db.String(200))
    precio = db.Column(db.Numeric(8, 2))
    detalles = db.relationship('DetallePedido', backref='pizza', lazy=True)

class Cliente(db.Model):
    __tablename__ = 'clientes' 
    id_cliente = db.Column(db.Integer, primary_key=True) 
    nombre = db.Column(db.String(100)) 
    direccion = db.Column(db.String(200)) 
    telefono = db.Column(db.String(20)) 
    pedidos = db.relationship('Pedido', backref='cliente', lazy=True)

class Pedido(db.Model):
    __tablename__ = 'pedidos'
    id_pedido = db.Column(db.Integer, primary_key=True)
    id_cliente = db.Column(db.Integer, db.ForeignKey('clientes.id_cliente'))
    fecha = db.Column(db.Date)
    total = db.Column(db.Numeric(10, 2))
    detalles = db.relationship('DetallePedido', backref='pedido', lazy=True)

class DetallePedido(db.Model):
    __tablename__ = 'detalle_pedido'
    id_detalle = db.Column(db.Integer, primary_key=True)
    
    id_pedido = db.Column(db.Integer, db.ForeignKey('pedidos.id_pedido'))
    id_pizza = db.Column(db.Integer, db.ForeignKey('pizzas.id_pizza'))
    cantidad = db.Column(db.Integer) 
    subtotal = db.Column(db.Numeric(10, 2))
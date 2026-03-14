from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, RadioField, SelectMultipleField, SubmitField
from wtforms import widgets
from wtforms.validators import DataRequired, NumberRange

class PedidoForm(FlaskForm):
    nombre = StringField('Nombre', validators=[DataRequired(message="El nombre es obligatorio")])
    direccion = StringField('Dirección', validators=[DataRequired()])
    telefono = StringField('Teléfono', validators=[DataRequired()])
    fecha = StringField('Fecha (dd-mm-yyyy)', validators=[DataRequired()])
    
    tamano = RadioField('Tamaño Pizza', choices=[
        ('Chica', 'Chica $40'), 
        ('Mediana', 'Mediana $80'), 
        ('Grande', 'Grande $120')
    ], validators=[DataRequired()])
    
    ingredientes = SelectMultipleField('Ingredientes', choices=[
        ('Jamon', 'Jamón $10'),
        ('Pina', 'Piña $10'),
        ('Champinones', 'Champiñones $10')
    ], 
    widget=widgets.ListWidget(prefix_label=False), 
    option_widget=widgets.CheckboxInput()
    ) 
    
    num_pizzas = IntegerField('Num. de Pizzas',default=1, validators=[DataRequired(), NumberRange(min=1)])
    agregar = SubmitField('Agregar')

class BusquedaForm(FlaskForm):
    tipo_busqueda = RadioField('Filtrar por', choices=[
        ('dia', 'Día de la semana'), 
        ('mes', 'Mes del año')
    ], default='dia')
    
    valor = StringField('Escribe el día o el mes', validators=[DataRequired()])
    buscar = SubmitField('Buscar Ventas')
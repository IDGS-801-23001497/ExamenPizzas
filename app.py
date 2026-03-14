from flask import Flask, render_template
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
from flask_migrate import Migrate, migrate
from models import db

from pedidos.routes import pedidos_bp

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)

csrf = CSRFProtect()
db.init_app(app)
migrate = Migrate(app, db)
app.register_blueprint(pedidos_bp)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    csrf.init_app(app)
    with app.app_context():
        db.create_all()
    app.run(debug=True)
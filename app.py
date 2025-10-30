from flask import Flask, render_template, request, redirect, url_for, flash
import json, os

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)
MATERIAS_FILE = os.path.join(DATA_DIR, 'materias_primas.json')
RECETAS_FILE = os.path.join(DATA_DIR, 'recetas.json')

def load_json(path, default):
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(default, f, ensure_ascii=False, indent=2)
        return default
    with open(path, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except Exception:
            return default

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

app = Flask(__name__)
app.secret_key = 'dev-secret-change-this'

@app.route('/')
def index():
    materias = load_json(MATERIAS_FILE, {})
    return render_template('index.html', materias=materias)

@app.route('/materias', methods=['GET', 'POST'])
def materias():
    materias = load_json(MATERIAS_FILE, {})
    if request.method == 'POST':
        accion = request.form.get('accion')
        nombre = request.form.get('nombre', '').strip()
        unidad = request.form.get('unidad', '').strip()
        precio = request.form.get('precio', '').strip()

        if accion == 'agregar':
            if not nombre:
                flash('El nombre es obligatorio.', 'danger')
            elif nombre in materias:
                flash('La materia prima ya existe.', 'warning')
            else:
                try:
                    precio_f = float(precio)
                except:
                    precio_f = 0.0
                materias[nombre] = {'unidad': unidad or '-', 'precio_unitario': precio_f}
                save_json(MATERIAS_FILE, materias)
                flash('Materia prima agregada.', 'success')
        elif accion == 'editar':
            original = request.form.get('original')
            if original and original in materias:
                try:
                    precio_f = float(precio)
                except:
                    precio_f = materias[original].get('precio_unitario', 0.0)
                # allow renaming
                if nombre and nombre != original:
                    materias.pop(original)
                key = nombre or original
                materias[key] = {'unidad': unidad or materias.get(original, {}).get('unidad','-'),
                                 'precio_unitario': precio_f}
                save_json(MATERIAS_FILE, materias)
                flash('Materia prima actualizada.', 'success')
        elif accion == 'eliminar':
            eliminar = request.form.get('eliminar')
            if eliminar and eliminar in materias:
                materias.pop(eliminar)
                save_json(MATERIAS_FILE, materias)
                flash('Materia prima eliminada.', 'success')
        return redirect(url_for('materias'))

    return render_template('materias.html', materias=materias)

@app.route('/receta', methods=['GET','POST'])
def receta():
    materias = load_json(MATERIAS_FILE, {})
    recetas = load_json(RECETAS_FILE, [])
    if request.method == 'POST':
        nombre_producto = request.form.get('nombre_producto','').strip()
        ingredientes = {}
        for key, value in request.form.items():
            if key.startswith('cant_'):
                materia = key[5:]
                if value.strip():
                    try:
                        cantidad = float(value)
                    except:
                        cantidad = 0.0
                    ingredientes[materia] = cantidad
        if not nombre_producto:
            flash('Nombre del producto es obligatorio.', 'danger')
        elif not ingredientes:
            flash('Agrega al menos un ingrediente con cantidad.', 'danger')
        else:
            receta_obj = {'nombre': nombre_producto, 'ingredientes': ingredientes}
            recetas.append(receta_obj)
            save_json(RECETAS_FILE, recetas)
            flash('Receta guardada.', 'success')
            return redirect(url_for('resultado', index=len(recetas)-1))

    return render_template('receta.html', materias=materias, recetas=recetas)

@app.route('/resultado/<int:index>')
def resultado(index):
    materias = load_json(MATERIAS_FILE, {})
    recetas = load_json(RECETAS_FILE, [])
    if index < 0 or index >= len(recetas):
        flash('Receta no encontrada.', 'danger')
        return redirect(url_for('receta'))
    receta = recetas[index]
    detalle = []
    costo_total = 0.0
    for ing, cant in receta['ingredientes'].items():
        if ing in materias:
            precio = float(materias[ing].get('precio_unitario', 0))
            unidad = materias[ing].get('unidad','-')
            costo = precio * cant
            detalle.append({'ingrediente': ing, 'cantidad': cant, 'unidad': unidad, 'precio_unitario': precio, 'costo': costo})
            costo_total += costo
        else:
            detalle.append({'ingrediente': ing, 'cantidad': cant, 'unidad': '?', 'precio_unitario': 0.0, 'costo': 0.0})

    return render_template('resultado.html', receta=receta, detalle=detalle, costo_total=costo_total)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

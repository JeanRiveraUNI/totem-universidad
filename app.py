from flask import Flask, render_template, request, redirect, session, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = 'QAZWSXEDCRFVTGBYHNUJMIKOLP'
# Configura la conexión con MongoDB
client = MongoClient('mongodb+srv://desarrollo2023:rFtSer5m5UVVuoYI@millenium.pardqk8.mongodb.net/')
db = client['millenium']
user_collection = db['users']
trabajadores_collection = db['trabajadores']
salas_collection = db['salas']
deportes_collection = db['deportes']

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    """
    Función que maneja la ruta '/dashboard' para el método GET y POST.
    Si la solicitud es POST, verifica las credenciales de inicio de sesión y redirige al perfil correspondiente.
    Si la solicitud es GET, muestra el formulario de inicio de sesión.

    Returns:
        Si la solicitud es POST y las credenciales son válidas:
            - Si el rol del usuario es 'admin', renderiza el perfil de administrador.
            - Si el rol del usuario es 'trabajador', renderiza el perfil de trabajador.
        Si la solicitud es POST y las credenciales son inválidas, renderiza un mensaje de error.
        Si la solicitud es GET, renderiza el formulario de inicio de sesión.
    """
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = user_collection.find_one({'username': username, 'password': password})
        if user:
            session['username'] = user['username']
            if user['rol'] == 'admin':
                trabajadores = trabajadores_collection.find()
                return render_template('admin_profile.html', username=username, trabajadores=trabajadores)
            elif user['rol'] == 'trabajador':
                trabajador = trabajadores_collection.find_one({'user_id': user['user_id']})
                return render_template('user_profile.html', username=username, trabajador=trabajador)
            else:
                return render_template('error.html', message='Rol de usuario no válido.')
        else:
            return render_template('error.html', message='Usuario o contraseña incorrectos.')

    # Si la solicitud es GET, simplemente renderiza el formulario de inicio de sesión
    return render_template('login.html')




@app.route('/certificados')
def certificados():
    # Redirecciona al sitio externo de certificados de Inacap
    return redirect('https://portales.inacap.cl/servicios-tecnologicos/servicios/intranet-estudiante/index')
@app.route('/user_profile')
def user_profile():
    # Lógica para mostrar el perfil del usuario
    # ...
    return render_template('user_profile.html')



@app.route('/Dae')
def dae():
    # Lógica para la página de DAE
    return render_template('Dae.html')

@app.route('/reservar', methods=['POST'])
def reservar():
    if request.method == 'POST':
        username = session.get('username')
        nombre_sala = request.form['salas']
        
        # Encuentra el documento de la sala por su nombre en la base de datos
        sala = salas_collection.find_one({'nombre': nombre_sala})
        if sala and sala['estado'] == 'libre':
            # Actualiza el estado de la sala a 'ocupada' y vincula al usuario
            salas_collection.update_one(
                {'nombre': nombre_sala, 'estado': 'libre'},
                {'$set': {'estado': 'ocupada', 'usuario': username}}
            )
            # Actualiza al usuario con la sala seleccionada en la sesión
            session['sala_seleccionada'] = nombre_sala
            return render_template('liberar.html', nombre_sala=nombre_sala)
        else:
            return redirect('/biblioteca')
        

@app.route('/liberar', methods=['POST'])
def liberar():
    if request.method == 'POST':
        username = session.get('username')
        nombre_sala = request.form['sala']
        
        # Verifica si la sala seleccionada está ocupada por el usuario actual
        sala = salas_collection.find_one({'nombre': nombre_sala, 'usuario': username})
        
        if sala:
            # Cambia el estado de la sala a 'libre' y elimina el vínculo con el usuario
            salas_collection.update_one(
                {'nombre': nombre_sala},
                {'$set': {'estado': 'libre', 'usuario': None}}
            )
            return render_template('user_profile.html', username=username)
        else:
            return 'No tienes permiso para liberar esta sala o la sala no está ocupada por ti.'


        
@app.route('/liberar-sala')
def liberar_sala():
    username = session.get('username')  # Obtén el nombre de usuario desde la sesión

    if username:
        # Busca la sala ocupada por el usuario según su username
        sala_ocupada = salas_collection.find_one({'usuario': username, 'estado': 'ocupada'})
        
        if sala_ocupada:
            nombre_sala = sala_ocupada['nombre']
            return render_template('liberar.html', nombre_sala=nombre_sala)
        else:
            return 'No tienes una sala ocupada actualmente.'
    
    return redirect('/')  # Si no hay un usuario autenticado, redirige al inicio de sesión



@app.route('/biblioteca')
def biblioteca():
    username = session.get('username')
    
    if username:
        
        sala_ocupada = salas_collection.find_one({'usuario': username, 'estado': 'ocupada'})

        if sala_ocupada:
            return redirect('/liberar-sala')
        # Obtén todas las salas disponibles
        salas_disponibles = salas_collection.find({'estado': 'libre'})
        return render_template('biblioteca.html', salas=salas_disponibles)
    
    return redirect('/')

    

@app.route('/deportes')
def deportes():
    username = session.get('username')

    if username:
        deporte_ocupado = deportes_collection.find_one({'usuario': username, 'estado': 'Ocupado'})

        if deporte_ocupado:
            return redirect('/liberar-deporte')  # Redirige si el usuario tiene un deporte ocupado

        deportes_disponibles = deportes_collection.find({'estado': 'Disponible'})
        return render_template('deportes.html', deportes=deportes_disponibles)
    else:
        return redirect('/')
    
@app.route('/liberardeporte', methods=['POST'])
def liberardeporte():
    if request.method == 'POST':
        username = session.get('username')
        nombre_deporte = request.form.get('deporte')  # Usa request.form.get() para evitar KeyError
        
        if nombre_deporte:
            # Verifica si el deporte seleccionado está ocupado por el usuario actual
            deportes = deportes_collection.find_one({'nombre': nombre_deporte, 'usuario': username})
            
            if deportes:
                # Cambia el estado del deporte a 'Disponible' y elimina el vínculo con el usuario
                deportes_collection.update_one(
                    {'nombre': nombre_deporte},
                    {'$set': {'estado': 'Disponible', 'usuario': None}}
                )
                return render_template('user_profile.html', username=username)
            else:
                return 'No tienes permiso para liberar este deporte o el deporte no está ocupado por ti.'
        else:
            return 'No se proporcionó el campo "deportes" en la solicitud.'

@app.route('/reservar-deporte', methods=['POST'])
def reservar_deporte():
    if request.method == 'POST':
        username = session.get('username')
        nombre_deporte = request.form['deportes']

        # Encuentra el documento del deporte por su nombre en la base de datos
        deporte = deportes_collection.find_one({'nombre': nombre_deporte})
        if deporte and deporte['estado'] == 'Disponible':
            # Actualiza el estado del deporte a 'Ocupado' y vincula al usuario
            deportes_collection.update_one(
                {'nombre': nombre_deporte, 'estado': 'Disponible'},
                {'$set': {'estado': 'Ocupado', 'usuario': username}}
            )
            session['deporte_seleccionado'] = nombre_deporte
            return render_template('deportes_liberado.html', nombre_deporte=nombre_deporte)
        else:
            return redirect('/deportes')  # Redirige a la página de deportes si no se puede reservar el deporte


@app.route('/liberar-deporte', methods=['GET', 'POST'])
def liberar_deporte():
    username = session.get('username')
    if username:
        # Tu lógica para liberar el deporte en caso de una solicitud POST
        deporte_ocupado = deportes_collection.find_one({'usuario': username, 'estado': 'Ocupado'})

        if deporte_ocupado:
            nombre_deporte = deporte_ocupado['nombre']
            return render_template('deportes_liberado.html', nombre_deporte=nombre_deporte)
        else:
            return 'No tienes un deporte ocupado actualmente.'

    return  redirect('/')

@app.route('/logout', methods=['POST'])
def logout():
    # Eliminar la sesión del usuario
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
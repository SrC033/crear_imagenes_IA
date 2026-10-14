"""
main.py - SERVIDOR FLASK CON TINYSD (HTML PRIMERO, MODELO DESPUÉS)
"""

import os
import sys
import atexit
import threading
import time
import queue
import uuid
from flask import Flask, render_template, request, jsonify

# ============================================================
# RUTA PRINCIPAL
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ============================================================
# AGREGAR MODULO IA AL PATH
# ============================================================

RUTA_MODULO_IA = os.path.join(BASE_DIR, "modulos", "ia")

if RUTA_MODULO_IA not in sys.path:
    sys.path.insert(0, RUTA_MODULO_IA)

# ============================================================
# IMPORTAR IA
# ============================================================

try:
    from ia import crear_ia
except Exception as e:
    print("=" * 60)
    print("ERROR IMPORTANDO ia.py")
    print(e)
    print("=" * 60)
    raise

# ============================================================
# FLASK
# ============================================================

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates")
)

# ============================================================
# CREAR IA
# ============================================================

print("=" * 60)
print("🚀 INICIANDO APLICACION CON TINYSD")
print("=" * 60)

ia = crear_ia()

# ============================================================
# ESTADO DE CARGA DEL MODELO
# ============================================================

modelo_precargado = False
modelo_precargado_lock = threading.Lock()
progreso_precarga = 0
mensaje_precarga = "Esperando..."
modelo_cargando = False
modelo_cargado_intentado = False

# ============================================================
# PRECARGA EN SEGUNDO PLANO (DESPUÉS DEL HTML)
# ============================================================

def precargar_modelo_background():
    """
    Precarga el modelo en segundo plano DESPUÉS de abrir el HTML
    """
    global modelo_precargado, progreso_precarga, mensaje_precarga, modelo_cargando, modelo_cargado_intentado
    
    modelo_cargando = True
    modelo_cargado_intentado = True
    
    print("=" * 60)
    print("🔄 PRECARGANDO MODELO (segundo plano)...")
    print("=" * 60)
    
    try:
        # Paso 1: Iniciar IA
        mensaje_precarga = "⚙️ Inicializando IA..."
        progreso_precarga = 10
        print(f"   {mensaje_precarga}")
        
        if not ia.iniciar():
            raise Exception("No se pudo iniciar la IA")
        
        time.sleep(0.3)
        
        # Paso 2: Cargar generador
        mensaje_precarga = "🎨 Cargando generador de imágenes..."
        progreso_precarga = 25
        print(f"   {mensaje_precarga}")
        
        if not ia._cargar_generador():
            raise Exception("No se pudo cargar el generador")
        
        time.sleep(0.3)
        
        # Paso 3: Cargar modelo TinySD
        mensaje_precarga = "🧠 Cargando modelo TinySD en memoria..."
        progreso_precarga = 40
        print(f"   {mensaje_precarga}")
        print("   ⏳ Esto puede tomar varios segundos...")
        
        inicio_carga = time.time()
        
        # Forzar carga con un prompt de prueba
        resultado_prueba = ia.generar_imagen("test", guardar=False)
        tiempo_carga = time.time() - inicio_carga
        
        if resultado_prueba.get('success'):
            print(f"   ✅ Modelo TinySD cargado en {tiempo_carga:.1f}s")
            progreso_precarga = 100
            mensaje_precarga = f"✅ Modelo listo ({tiempo_carga:.1f}s)"
            
            with modelo_precargado_lock:
                modelo_precargado = True
                modelo_cargando = False
        else:
            raise Exception(resultado_prueba.get('error', 'Error al cargar el modelo'))
        
        print("=" * 60)
        print("✅ MODELO PRECARGADO CORRECTAMENTE")
        print("=" * 60)
        
    except Exception as e:
        mensaje_precarga = f"⚠️ Error: {str(e)}"
        progreso_precarga = 100
        modelo_cargando = False
        print(f"   {mensaje_precarga}")
        print("=" * 60)
        print("⚠️  EL MODELO SE CARGARÁ AL GENERAR LA PRIMERA IMAGEN")
        print("=" * 60)

# ============================================================
# COLA DE TAREAS ASÍNCRONAS
# ============================================================

task_queue = queue.Queue()
task_results = {}
task_status = {}
task_lock = threading.Lock()

class TaskStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    LOADING_MODEL = "loading_model"
    GENERATING = "generating"
    COMPLETED = "completed"
    ERROR = "error"

def process_task_worker():
    """Worker que procesa las tareas en segundo plano"""
    while True:
        try:
            task_id, task_type, data = task_queue.get(timeout=1)
            
            with task_lock:
                task_status[task_id] = {
                    "status": TaskStatus.PROCESSING,
                    "progress": 0,
                    "message": "Iniciando procesamiento...",
                    "steps": []
                }
            
            if task_type == "generate_image":
                _process_generation(task_id, data)
            
            task_queue.task_done()
            
        except queue.Empty:
            continue
        except Exception as e:
            print(f"❌ Error en worker: {e}")
            with task_lock:
                if task_id in task_status:
                    task_status[task_id]["status"] = TaskStatus.ERROR
                    task_status[task_id]["error"] = str(e)

def _process_generation(task_id, data):
    """Procesa la generación de imagen en segundo plano"""
    try:
        prompt = data.get("prompt", "")
        guardar = data.get("guardar", False)
        
        global modelo_precargado
        
        if modelo_precargado:
            with task_lock:
                task_status[task_id]["status"] = TaskStatus.GENERATING
                task_status[task_id]["progress"] = 50
                task_status[task_id]["message"] = "Generando imagen (modelo precargado)..."
                task_status[task_id]["steps"] = [
                    {"id": 1, "title": "📥 Recibiendo prompt", "desc": prompt[:50], "status": "done"},
                    {"id": 2, "title": "✅ Modelo precargado", "desc": "Listo en memoria", "status": "done"},
                    {"id": 3, "title": "🖼️ Generando imagen", "desc": "Inferencia en progreso...", "status": "active"}
                ]
        else:
            with task_lock:
                task_status[task_id]["status"] = TaskStatus.LOADING_MODEL
                task_status[task_id]["progress"] = 10
                task_status[task_id]["message"] = "Cargando modelo TinySD (primera vez)..."
                task_status[task_id]["steps"] = [
                    {"id": 1, "title": "📥 Recibiendo prompt", "desc": prompt[:50], "status": "done"},
                    {"id": 2, "title": "🎨 Cargando modelo", "desc": "Preparando pipeline...", "status": "active"}
                ]
        
        start_time = time.time()
        resultado = ia.generar_imagen(prompt, guardar=guardar)
        elapsed = time.time() - start_time
        
        if resultado.get('success'):
            with task_lock:
                task_status[task_id]["progress"] = 100
                task_status[task_id]["status"] = TaskStatus.COMPLETED
                task_status[task_id]["message"] = f"✅ Imagen generada en {elapsed:.1f}s"
                task_status[task_id]["steps"] = [
                    {"id": 1, "title": "📥 Recibiendo prompt", "desc": prompt[:50], "status": "done"},
                    {"id": 2, "title": "🎨 Modelo listo", "desc": "Pipeline cargado", "status": "done"},
                    {"id": 3, "title": "🖼️ Generando imagen", "desc": "Inferencia completada", "status": "done"},
                    {"id": 4, "title": "💾 Preparando resultado", "desc": "Imagen lista", "status": "done"}
                ]
            
            task_results[task_id] = {
                "success": True,
                "imagen": resultado.get("imagen"),
                "nombre": resultado.get("nombre"),
                "ruta": resultado.get("ruta"),
                "tiempo": elapsed,
                "seed": resultado.get("seed"),
                "prompt_traducido": resultado.get("prompt_traducido")
            }
        else:
            with task_lock:
                task_status[task_id]["status"] = TaskStatus.ERROR
                task_status[task_id]["progress"] = 100
                task_status[task_id]["message"] = f"❌ Error: {resultado.get('error', 'Error desconocido')}"
                task_status[task_id]["error"] = resultado.get("error", "Error desconocido")
            
    except Exception as e:
        print(f"❌ Error en _process_generation: {e}")
        import traceback
        traceback.print_exc()
        with task_lock:
            task_status[task_id]["status"] = TaskStatus.ERROR
            task_status[task_id]["progress"] = 100
            task_status[task_id]["message"] = f"❌ Error: {str(e)}"
            task_status[task_id]["error"] = str(e)

# ============================================================
# INICIAR WORKER
# ============================================================

worker_thread = threading.Thread(target=process_task_worker, daemon=True)
worker_thread.start()

# ============================================================
# RUTAS
# ============================================================

@app.route("/")
def index():
    return render_template("main.html")

@app.route("/api/estado", methods=["GET"])
def estado():
    try:
        activo = ia.esta_activo()
        modo = ia.obtener_modo() if hasattr(ia, 'obtener_modo') else "desconocido"
        generador_cargado = ia.generador_cargado if hasattr(ia, 'generador_cargado') else False

        return jsonify({
            "success": True,
            "activo": activo,
            "modelo": "TinySD",
            "modo": modo,
            "generador_cargado": generador_cargado,
            "device": "cpu",
            "precargado": modelo_precargado,
            "progreso_precarga": progreso_precarga,
            "mensaje_precarga": mensaje_precarga,
            "cargando": modelo_cargando
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "activo": False,
            "error": str(e)
        })

@app.route("/api/generar_imagen", methods=["POST"])
def generar_imagen():
    """Inicia una tarea de generación de imagen asíncrona"""
    try:
        data = request.get_json(silent=True)

        if not data:
            return jsonify({"success": False, "error": "No se recibieron datos."}), 400

        prompt = data.get("prompt", "").strip()
        guardar = data.get("guardar", False)

        if not prompt:
            return jsonify({"success": False, "error": "Se requiere un prompt."}), 400

        task_id = str(uuid.uuid4())
        
        with task_lock:
            task_status[task_id] = {
                "status": TaskStatus.PENDING,
                "progress": 0,
                "message": "Tarea en cola...",
                "steps": []
            }
        
        task_queue.put((task_id, "generate_image", {"prompt": prompt, "guardar": guardar}))
        
        print(f"📋 Tarea {task_id[:8]} encolada: {prompt[:50]}...")
        
        return jsonify({
            "success": True,
            "task_id": task_id,
            "message": "Tarea iniciada correctamente"
        })

    except Exception as e:
        print(f"ERROR: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/tarea/<task_id>", methods=["GET"])
def obtener_tarea(task_id):
    """Obtiene el estado de una tarea"""
    try:
        with task_lock:
            if task_id not in task_status:
                return jsonify({"success": False, "error": "Tarea no encontrada"}), 404
            
            status = task_status[task_id].copy()
            
            if status["status"] == TaskStatus.COMPLETED and task_id in task_results:
                status["result"] = task_results[task_id]
            
            return jsonify({
                "success": True,
                "task": status
            })
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/guardar_imagen", methods=["POST"])
def guardar_imagen():
    try:
        data = request.get_json(silent=True)
        
        if not data:
            return jsonify({"success": False, "error": "No se recibieron datos."}), 400
        
        nombre = data.get("nombre", None)
        
        resultado = ia.guardar_imagen_actual(nombre)
        
        return jsonify(resultado)
        
    except Exception as e:
        print("ERROR:", e)
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/limpiar", methods=["POST"])
def limpiar():
    try:
        ia.limpiar_historial()
        return jsonify({"success": True, "mensaje": "Historial limpiado."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============================================================
# DETENER IA AL CERRAR
# ============================================================

def cerrar():
    print("\nDeteniendo IA...")
    try:
        ia.detener()
    except Exception as e:
        print("Error deteniendo IA:", e)

atexit.register(cerrar)

# ============================================================
# ABRIR VENTANA NATIVA (PRIMERO)
# ============================================================

def abrir_ventana_nativa():
    """Abre la aplicación en una ventana nativa"""
    import time
    
    print("=" * 60)
    print("🪟 ABRIENDO VENTANA NATIVA")
    print("=" * 60)
    
    try:
        import webview
        
        print("✅ pywebview encontrado")
        print("📐 Creando ventana 1200x800...")
        
        window = webview.create_window(
            'AI Studio - Generador de Imágenes',
            'http://127.0.0.1:5000',
            width=1200,
            height=800,
            resizable=True,
            min_size=(900, 600),
            confirm_close=True,
            fullscreen=False
        )
        
        print("✅ Ventana creada correctamente")
        
        def maximizar():
            time.sleep(1)
            try:
                window.maximize()
                print("✅ Ventana maximizada")
            except:
                pass
        
        threading.Thread(target=maximizar, daemon=True).start()
        
        print("🚀 Iniciando webview...")
        webview.start(gui='edgechromium', debug=False)
        
    except ImportError:
        print("⚠️ pywebview no instalado. Instalando...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "pywebview"], check=True)
        abrir_ventana_nativa()
        
    except Exception as e:
        print(f"❌ Error abriendo ventana: {e}")
        import webbrowser
        webbrowser.open('http://127.0.0.1:5000')

# ============================================================
# EJECUTAR
# ============================================================

if __name__ == "__main__":
    print()
    print("=" * 60)
    print("🚀 TINYSD - GENERADOR DE IMÁGENES")
    print("=" * 60)
    print("🌐 Servidor: http://127.0.0.1:5000")
    print("=" * 60)
    print()

    # ============================================================
    # PASO 1: Iniciar servidor Flask en segundo plano
    # ============================================================
    server_thread = threading.Thread(
        target=lambda: app.run(
            host="127.0.0.1",
            port=5000,
            debug=False,
            threaded=True,
            use_reloader=False
        ),
        daemon=True
    )
    server_thread.start()
    
    print("⏳ Iniciando servidor...")
    time.sleep(2)
    print("✅ Servidor listo")
    
    # ============================================================
    # PASO 2: PRECARGAR MODELO EN SEGUNDO PLANO
    # (Mientras el HTML se abre, el modelo se carga por detrás)
    # ============================================================
    print("")
    print("=" * 60)
    print("🔄 Iniciando precarga del modelo EN SEGUNDO PLANO...")
    print("   (La ventana se abrirá inmediatamente)")
    print("=" * 60)
    print("")
    
    precarga_thread = threading.Thread(
        target=precargar_modelo_background,
        daemon=True
    )
    precarga_thread.start()
    
    # ============================================================
    # PASO 3: Abrir ventana nativa INMEDIATAMENTE
    # (El modelo se sigue cargando en segundo plano)
    # ============================================================
    abrir_ventana_nativa()
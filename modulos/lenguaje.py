"""
descargar_lenguaje.py - Descarga modelo de traducción español→inglés (PORTABLE)
"""

import os
import sys
import shutil
import subprocess
import time

# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_TRADUCCION = os.path.join(BASE_DIR, "modelo", "lenguaje_traduccion")

# Crear carpeta si no existe
os.makedirs(RUTA_TRADUCCION, exist_ok=True)

# Configurar variables de entorno para Argos Translate
os.environ["ARGOS_DATA_DIR"] = RUTA_TRADUCCION
os.environ["ARGOS_CACHE_DIR"] = os.path.join(RUTA_TRADUCCION, "cache")
os.environ["ARGOS_HOME"] = RUTA_TRADUCCION

print("=" * 60)
print("📥 DESCARGA DE MODELO DE TRADUCCIÓN (español → inglés)")
print("=" * 60)
print(f"📁 Destino: {RUTA_TRADUCCION}")
print("")

# ============================================================
# INSTALAR ARGOS TRANSLATE SI NO ESTÁ
# ============================================================

def instalar_argos():
    """Instala argostranslate si no está disponible"""
    try:
        import argostranslate
        print("✅ Argos Translate ya está instalado")
        return True
    except ImportError:
        print("⚠️ Argos Translate no está instalado. Instalando...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "argostranslate"], check=True)
            print("✅ Argos Translate instalado correctamente")
            return True
        except Exception as e:
            print(f"❌ Error instalando Argos Translate: {e}")
            return False

# ============================================================
# DESCARGAR MODELO DE TRADUCCIÓN (VERSIÓN CORREGIDA)
# ============================================================

def descargar_modelo_traduccion():
    """Descarga el modelo de traducción español→inglés en la carpeta local"""
    
    print("📦 Descargando modelo de traducción (español → inglés)...")
    print("   ⏳ Esto puede tomar unos minutos...")
    print("")
    
    try:
        import argostranslate.package
        import argostranslate.translate
        
        # Actualizar índice de paquetes
        print("   🔄 Actualizando índice de paquetes...")
        argostranslate.package.update_package_index()
        
        # Obtener lista de paquetes disponibles
        available_packages = argostranslate.package.get_available_packages()
        
        print(f"   📋 Paquetes disponibles: {len(available_packages)}")
        
        # Buscar el paquete español → inglés
        package_to_install = None
        for pkg in available_packages:
            if pkg.from_code == "es" and pkg.to_code == "en":
                package_to_install = pkg
                break
        
        if package_to_install is None:
            print("   ❌ No se encontró el paquete de traducción español → inglés")
            print("   📋 Paquetes disponibles:")
            for pkg in available_packages[:10]:
                print(f"      - {pkg.from_code} → {pkg.to_code} ({pkg.name})")
            return False
        
        print(f"   ✅ Paquete encontrado: {package_to_install.from_code} → {package_to_install.to_code}")
        print(f"   📦 Nombre: {package_to_install.name}")
        
        # Intentar obtener el tamaño de forma segura
        try:
            if hasattr(package_to_install, 'size'):
                print(f"   📦 Tamaño: ~{package_to_install.size / (1024*1024):.1f} MB")
            elif hasattr(package_to_install, 'package_size'):
                print(f"   📦 Tamaño: ~{package_to_install.package_size / (1024*1024):.1f} MB")
            else:
                print(f"   📦 Tamaño: desconocido (descargando...)")
        except:
            print(f"   📦 Tamaño: desconocido (descargando...)")
        
        # Descargar el paquete
        print(f"   ⬇️ Descargando...")
        download_path = package_to_install.download()
        
        # Instalar en la carpeta local
        print(f"   📁 Instalando en: {RUTA_TRADUCCION}")
        argostranslate.package.install_from_path(download_path)
        
        # Verificar instalación
        print("   ✅ Modelo instalado correctamente")
        
        # Verificar archivos descargados
        archivos = os.listdir(RUTA_TRADUCCION)
        print(f"   📄 Archivos en {RUTA_TRADUCCION}:")
        for archivo in archivos:
            ruta_completa = os.path.join(RUTA_TRADUCCION, archivo)
            if os.path.isdir(ruta_completa):
                # Contar archivos en la carpeta
                try:
                    num_archivos = len(os.listdir(ruta_completa))
                    print(f"      - {archivo}/ ({num_archivos} archivos)")
                except:
                    print(f"      - {archivo}/")
            else:
                tamaño = os.path.getsize(ruta_completa)
                if tamaño > 1024 * 1024:
                    print(f"      - {archivo} ({tamaño / (1024*1024):.1f} MB)")
                else:
                    print(f"      - {archivo} ({tamaño / 1024:.1f} KB)")
        
        # Probar traducción
        print("")
        print("🧪 Probando traducción...")
        try:
            prueba = argostranslate.translate.translate("Hola mundo, ¿cómo estás?", "es", "en")
            print(f"   Español: 'Hola mundo, ¿cómo estás?'")
            print(f"   Inglés: '{prueba}'")
            
            if prueba and prueba != "Hola mundo, ¿cómo estás?":
                print("   ✅ Prueba exitosa!")
            else:
                print("   ⚠️ La prueba no devolvió traducción válida")
        except Exception as e:
            print(f"   ⚠️ Error en prueba: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error descargando modelo: {e}")
        import traceback
        traceback.print_exc()
        return False

# ============================================================
# MÉTODO ALTERNATIVO: USAR HUGGING FACE
# ============================================================

def descargar_desde_huggingface():
    """Método alternativo para descargar modelo de traducción desde Hugging Face"""
    
    print("📦 Descargando modelo desde Hugging Face...")
    
    try:
        # Intentar con transformers
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        import torch
        
        model_name = "Helsinki-NLP/opus-mt-es-en"
        
        print(f"   📁 Modelo: {model_name}")
        print("   ⬇️ Descargando... (puede tomar varios minutos)")
        
        # Descargar tokenizer y modelo
        tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=RUTA_TRADUCCION)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name, cache_dir=RUTA_TRADUCCION)
        
        print("   ✅ Modelo descargado correctamente")
        
        # Probar traducción
        print("")
        print("🧪 Probando traducción...")
        texto = "Hola mundo, ¿cómo estás?"
        inputs = tokenizer(texto, return_tensors="pt", truncation=True)
        outputs = model.generate(**inputs)
        traduccion = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        print(f"   Español: '{texto}'")
        print(f"   Inglés: '{traduccion}'")
        print("   ✅ Prueba exitosa!")
        
        return True
        
    except ImportError:
        print("   ⚠️ transformers no instalado. Instalando...")
        subprocess.run([sys.executable, "-m", "pip", "install", "transformers", "torch"], check=True)
        return descargar_desde_huggingface()
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

# ============================================================
# VERIFICAR MODELO
# ============================================================

def verificar_modelo():
    """Verifica que el modelo de traducción esté instalado correctamente"""
    print("")
    print("🔍 Verificando modelo de traducción...")
    
    # Buscar archivos .argosmodel
    archivos_modelo = []
    for root, dirs, files in os.walk(RUTA_TRADUCCION):
        for file in files:
            if file.endswith('.argosmodel') or file.endswith('.bin') or file.endswith('.safetensors'):
                archivos_modelo.append(os.path.join(root, file))
    
    if archivos_modelo:
        print(f"   ✅ Modelo encontrado: {len(archivos_modelo)} archivo(s)")
        for archivo in archivos_modelo[:5]:  # Mostrar primeros 5
            tamaño = os.path.getsize(archivo) / (1024*1024)
            print(f"      - {os.path.basename(archivo)} ({tamaño:.1f} MB)")
        if len(archivos_modelo) > 5:
            print(f"      ... y {len(archivos_modelo) - 5} archivos más")
        return True
    else:
        print("   ❌ No se encontraron modelos de traducción")
        return False

# ============================================================
# FUNCIÓN PARA REINSTALAR (OPCIONAL)
# ============================================================

def limpiar_modelo():
    """Limpia los modelos de traducción descargados"""
    print("")
    respuesta = input("¿Eliminar todos los modelos de traducción? (s/n): ")
    if respuesta.lower() in ['s', 'si', 'y', 'yes']:
        for archivo in os.listdir(RUTA_TRADUCCION):
            ruta = os.path.join(RUTA_TRADUCCION, archivo)
            try:
                if os.path.isdir(ruta):
                    shutil.rmtree(ruta)
                else:
                    os.remove(ruta)
                print(f"   🗑️ Eliminado: {archivo}")
            except Exception as e:
                print(f"   ⚠️ Error eliminando {archivo}: {e}")
        print("✅ Modelos eliminados")

# ============================================================
# PRINCIPAL
# ============================================================

if __name__ == "__main__":
    print()
    print("📋 ¿Qué quieres hacer?")
    print("   1. Descargar modelo de traducción (Argos Translate - recomendado)")
    print("   2. Descargar modelo desde Hugging Face (alternativa)")
    print("   3. Verificar modelo instalado")
    print("   4. Limpiar modelos descargados")
    print("   5. Salir")
    print()
    
    try:
        opcion = input("Selecciona una opción (1-5): ").strip()
    except:
        opcion = "1"
    
    if opcion == "1":
        # Instalar Argos si es necesario
        if instalar_argos():
            # Descargar modelo
            if descargar_modelo_traduccion():
                print("")
                print("=" * 60)
                print("✅ DESCARGA COMPLETADA")
                print(f"📁 Modelo guardado en: {RUTA_TRADUCCION}")
                print("=" * 60)
                print("")
                print("📝 La traducción ya está configurada en generar_imagen.py")
                print("   Simplemente escribe en español y se traducirá automáticamente.")
                print("")
            else:
                print("❌ Error en la descarga")
                print("")
                print("🔧 Intentando método alternativo...")
                if descargar_desde_huggingface():
                    print("✅ Modelo descargado desde Hugging Face")
        else:
            print("❌ No se pudo instalar Argos Translate")
    
    elif opcion == "2":
        if descargar_desde_huggingface():
            print("")
            print("=" * 60)
            print("✅ DESCARGA COMPLETADA")
            print(f"📁 Modelo guardado en: {RUTA_TRADUCCION}")
            print("=" * 60)
    
    elif opcion == "3":
        verificar_modelo()
    
    elif opcion == "4":
        limpiar_modelo()
    
    else:
        print("👋 Hasta luego!")
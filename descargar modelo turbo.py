"""
descargar_modelo_turbo.py - Descarga TinySD Turbo (100% LOCAL)
"""

import os
import sys
import subprocess
import shutil

# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_DESTINO = os.path.join(BASE_DIR, "modelo", "tiny-sd-turbo")

print("=" * 60)
print("📥 DESCARGA DE TinySD TURBO (LOCAL)")
print("=" * 60)
print(f"📁 Destino: {RUTA_DESTINO}")
print("")

# ============================================================
# DESCARGAR MODELO TURBO
# ============================================================

def descargar_modelo():
    """Descarga TinySD Turbo usando huggingface-hub"""
    
    print("📦 Descargando TinySD Turbo...")
    print("   Modelo: segmind/tiny-sd-turbo")
    print("   Tamaño: ~500 MB")
    print("   ⏳ Puede tomar varios minutos...")
    
    try:
        from huggingface_hub import snapshot_download
        
        # Eliminar carpeta si existe
        if os.path.exists(RUTA_DESTINO):
            print("🗑️ Eliminando versión anterior...")
            shutil.rmtree(RUTA_DESTINO)
        
        # Descargar modelo
        snapshot_download(
            repo_id="segmind/tiny-sd-turbo",
            local_dir=RUTA_DESTINO,
            local_dir_use_symlinks=False,
            allow_patterns=[
                "*.json",
                "*.txt",
                "*.md",
                "*.safetensors",
                "*.bin",
                "tokenizer/*",
                "scheduler/*",
                "unet/*",
                "vae/*",
                "text_encoder/*"
            ],
            resume_download=True,
            max_workers=4
        )
        
        print("")
        print("=" * 60)
        print("✅ DESCARGA COMPLETADA")
        print(f"📁 Modelo en: {RUTA_DESTINO}")
        print("=" * 60)
        print("")
        print("🚀 Ahora puedes generar imágenes en 2-5 segundos!")
        print("   Ejecuta: python main.py")
        print("")
        
        return True
        
    except ImportError:
        print("⚠️ huggingface-hub no instalado. Instalando...")
        subprocess.run([sys.executable, "-m", "pip", "install", "huggingface-hub"], check=True)
        return descargar_modelo()
        
    except Exception as e:
        print(f"❌ Error descargando: {e}")
        print("")
        print("🔧 Soluciones:")
        print("   1. Verifica tu conexión a internet")
        print("   2. Instala manualmente:")
        print(f"      pip install huggingface-hub")
        print(f"      huggingface-cli download segmind/tiny-sd-turbo --local-dir {RUTA_DESTINO}")
        return False

# ============================================================
# VERIFICAR MODELO
# ============================================================

def verificar_modelo():
    """Verifica que el modelo se descargó correctamente"""
    print("")
    print("🔍 Verificando modelo...")
    
    archivos_requeridos = [
        "model_index.json",
        "unet/diffusion_pytorch_model.safetensors",
        "vae/diffusion_pytorch_model.safetensors",
        "text_encoder/model.safetensors"
    ]
    
    faltantes = []
    for archivo in archivos_requeridos:
        ruta = os.path.join(RUTA_DESTINO, archivo)
        if not os.path.exists(ruta):
            faltantes.append(archivo)
        else:
            tamanio = os.path.getsize(ruta) / (1024**2)
            print(f"   ✅ {archivo} ({tamanio:.1f} MB)")
    
    if faltantes:
        print("")
        print("⚠️ Archivos faltantes:")
        for f in faltantes:
            print(f"      - {f}")
        return False
    
    print("")
    print("✅ Todos los archivos necesarios están presentes")
    return True

# ============================================================
# LIMPIAR ARCHIVOS INNECESARIOS
# ============================================================

def limpiar_descarga():
    """Elimina archivos innecesarios"""
    print("")
    print("🧹 Limpiando archivos innecesarios...")
    
    archivos_a_eliminar = [
        "*.png", "*.jpg", "*.jpeg", "*.gif",
        "*.mp4", "*.webm", "*.ogv"
    ]
    
    import glob
    eliminados = 0
    for patron in archivos_a_eliminar:
        for archivo in glob.glob(os.path.join(RUTA_DESTINO, patron)):
            try:
                os.remove(archivo)
                eliminados += 1
            except:
                pass
    
    if eliminados > 0:
        print(f"   🗑️ Eliminados {eliminados} archivos innecesarios")
    else:
        print("   ✅ No hay archivos innecesarios")

# ============================================================
# PRINCIPAL
# ============================================================

if __name__ == "__main__":
    print("")
    print("📋 ¿Descargar TinySD Turbo?")
    print("   - Genera imágenes en 2-5 segundos en CPU")
    print("   - Tamaño: ~500 MB")
    print("")
    
    try:
        respuesta = input("¿Continuar? (s/n): ").strip().lower()
    except:
        respuesta = "s"
    
    if respuesta == "s" or respuesta == "si" or respuesta == "y":
        if descargar_modelo():
            verificar_modelo()
            limpiar_descarga()
        else:
            print("❌ Descarga fallida")
    else:
        print("❌ Descarga cancelada")
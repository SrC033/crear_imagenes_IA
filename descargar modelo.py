"""
descargar_modelo.py - Descarga TinySD desde Hugging Face
"""

import os
import sys
import time
import subprocess
import shutil
from pathlib import Path

# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_DESTINO = os.path.join(BASE_DIR, "tiny-sd")

print("=" * 60)
print("📥 DESCARGA DE TinySD")
print("=" * 60)
print(f"📁 Descargando a: {RUTA_DESTINO}")

# ============================================================
# MÉTODO 1: Usar huggingface-hub (recomendado)
# ============================================================

def descargar_con_hub():
    """Descarga usando huggingface-hub (más rápido y confiable)"""
    print("\n📦 Opción 1: Usando huggingface-hub...")
    
    try:
        from huggingface_hub import snapshot_download
        
        print("   ⏳ Descargando modelo (puede tomar varios minutos)...")
        print("   📦 Tamaño: ~1.5 GB")
        
        # Descargar solo los archivos necesarios
        snapshot_download(
            repo_id="segmind/tiny-sd",
            local_dir=RUTA_DESTINO,
            local_dir_use_symlinks=False,
            allow_patterns=[
                "*.json",
                "*.txt",
                "*.md",
                "*.bin",
                "*.safetensors",
                "tokenizer/*",
                "scheduler/*"
            ],
            ignore_patterns=[
                "*.png",
                "*.jpg",
                "*.jpeg",
                "*.mp4",
                "*.webm",
                "*.gif"
            ],
            resume_download=True,
            max_workers=4
        )
        
        print(f"✅ Modelo descargado en: {RUTA_DESTINO}")
        return True
        
    except ImportError:
        print("   ⚠️ huggingface-hub no instalado. Instalando...")
        subprocess.run([sys.executable, "-m", "pip", "install", "huggingface-hub"], check=True)
        return descargar_con_hub()
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

# ============================================================
# MÉTODO 2: Usar requests (alternativa)
# ============================================================

def descargar_con_requests():
    """Descarga archivos individuales con requests (más lento)"""
    print("\n📦 Opción 2: Usando requests (alternativa)...")
    
    try:
        import requests
        import json
        
        os.makedirs(RUTA_DESTINO, exist_ok=True)
        
        # Lista de archivos necesarios
        archivos = [
            "model_index.json",
            "README.md",
            "config.json",
        ]
        
        # Archivos grandes (se descargan por separado)
        carpetas = [
            "unet",
            "vae", 
            "text_encoder",
            "tokenizer",
            "scheduler"
        ]
        
        # Descargar archivos pequeños
        for archivo in archivos:
            url = f"https://huggingface.co/segmind/tiny-sd/resolve/main/{archivo}"
            ruta = os.path.join(RUTA_DESTINO, archivo)
            
            if os.path.exists(ruta) and os.path.getsize(ruta) > 100:
                print(f"   ⏭️ {archivo} ya existe")
                continue
            
            print(f"   ⏳ Descargando: {archivo}")
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                with open(ruta, "wb") as f:
                    for chunk in response.iter_content(chunk_size=1024*1024):
                        if chunk:
                            f.write(chunk)
                print(f"   ✅ {archivo} descargado")
            else:
                print(f"   ⚠️ Error descargando {archivo}: {response.status_code}")
        
        print(f"✅ Archivos descargados en: {RUTA_DESTINO}")
        return True
        
    except ImportError:
        print("   ⚠️ requests no instalado. Instalando...")
        subprocess.run([sys.executable, "-m", "pip", "install", "requests"], check=True)
        return descargar_con_requests()
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

# ============================================================
# VERIFICAR DESCARGA
# ============================================================

def verificar_descarga():
    """Verifica que el modelo se descargó correctamente"""
    print("\n🔍 Verificando descarga...")
    
    archivos_requeridos = [
        "model_index.json",
        "unet/diffusion_pytorch_model.bin",
        "vae/diffusion_pytorch_model.bin",
        "text_encoder/pytorch_model.bin"
    ]
    
    faltantes = []
    for archivo in archivos_requeridos:
        ruta = os.path.join(RUTA_DESTINO, archivo)
        if not os.path.exists(ruta):
            faltantes.append(archivo)
        else:
            tamanio = os.path.getsize(ruta) / (1024**3)
            print(f"   ✅ {archivo} ({tamanio:.2f} GB)")
    
    if faltantes:
        print("\n   ⚠️ Archivos faltantes:")
        for f in faltantes:
            print(f"      - {f}")
        return False
    
    print("\n✅ Todos los archivos necesarios están presentes")
    return True

# ============================================================
# LIMPIAR CARPETAS INNECESARIAS
# ============================================================

def limpiar_descarga():
    """Elimina archivos innecesarios (imágenes, etc.)"""
    print("\n🧹 Limpiando archivos innecesarios...")
    
    # Archivos a eliminar
    a_eliminar = [
        "*.png",
        "*.jpg", 
        "*.jpeg",
        "*.gif",
        "*.mp4",
        "*.webm"
    ]
    
    # Buscar y eliminar
    import glob
    for patron in a_eliminar:
        for archivo in glob.glob(os.path.join(RUTA_DESTINO, patron)):
            try:
                os.remove(archivo)
                print(f"   🗑️ Eliminado: {os.path.basename(archivo)}")
            except:
                pass
    
    print("✅ Limpieza completada")

# ============================================================
# PRINCIPAL
# ============================================================

if __name__ == "__main__":
    print()
    
    # Preguntar método
    print("📋 ¿Cómo quieres descargar?")
    print("   1. Usando huggingface-hub (recomendado, más rápido)")
    print("   2. Usando requests (alternativa, más lento)")
    
    try:
        opcion = input("\nSelecciona una opción (1/2): ").strip()
    except:
        opcion = "1"
    
    if opcion == "1":
        exito = descargar_con_hub()
    else:
        exito = descargar_con_requests()
    
    if exito:
        # Verificar
        verificar_descarga()
        
        # Limpiar archivos innecesarios
        limpiar_descarga()
        
        print("\n" + "=" * 60)
        print("✅ DESCARGA COMPLETADA")
        print(f"📁 Modelo en: {RUTA_DESTINO}")
        print("=" * 60)
        
        # Mostrar uso
        print("\n📝 Para usar el modelo:")
        print(f"   from diffusers import DiffusionPipeline")
        print(f"   pipe = DiffusionPipeline.from_pretrained('{RUTA_DESTINO}')")
        print()
    else:
        print("\n❌ Error en la descarga. Intenta manualmente:")
        print(f"   git clone https://huggingface.co/segmind/tiny-sd {RUTA_DESTINO}")
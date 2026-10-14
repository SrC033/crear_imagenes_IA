"""
generar_imagen.py - Generador de imágenes con TinySD (CALIDAD EXTREMA)
"""

import os
import sys
import time
import base64
import torch
from diffusers import DiffusionPipeline
from PIL import Image, ImageEnhance, ImageFilter
import io
import warnings
import re
from typing import Tuple

warnings.filterwarnings("ignore")

# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELO_PATH = os.path.join(BASE_DIR, "modelo", "tiny-sd")
IMAGENES_PATH = os.path.join(BASE_DIR, "modelo", "imagenes")

os.makedirs(IMAGENES_PATH, exist_ok=True)

# ============================================================
# TRADUCCIÓN CON translators
# ============================================================

_traductor_disponible = False

def verificar_traductor():
    """Verifica e inicializa el traductor"""
    global _traductor_disponible
    
    try:
        import translators as ts
        prueba = ts.google("hola", from_language='es', to_language='en')
        if prueba:
            _traductor_disponible = True
            print("   ✅ translators disponible y funcionando")
            return True
    except ImportError:
        print("   ⚠️ translators no instalado. Instalando...")
        try:
            import subprocess
            subprocess.run([sys.executable, "-m", "pip", "install", "translators"], 
                         capture_output=True, check=True)
            import translators as ts
            _traductor_disponible = True
            print("   ✅ translators instalado y funcionando")
            return True
        except Exception as e:
            print(f"   ❌ Error instalando translators: {e}")
            return False
    except Exception as e:
        print(f"   ⚠️ Error con translators: {e}")
        return False

def traducir_online(texto: str) -> str:
    """Traduce texto del español al inglés usando translators"""
    global _traductor_disponible
    
    if not texto or not texto.strip():
        return texto
    
    if not _traductor_disponible:
        if not verificar_traductor():
            return texto
    
    try:
        import translators as ts
        
        resultado = ts.google(
            texto, 
            from_language='es', 
            to_language='en',
            timeout=10
        )
        
        if resultado and resultado != texto:
            return resultado
        else:
            return texto
            
    except Exception as e:
        print(f"   ⚠️ Error en traducción: {e}")
        try:
            import translators as ts
            resultado = ts.bing(texto, from_language='es', to_language='en')
            if resultado and resultado != texto:
                return resultado
        except:
            pass
        
        return texto

# ============================================================
# DETECCIÓN DE IDIOMA
# ============================================================

PALABRAS_ESPANOL = {
    'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas',
    'de', 'en', 'a', 'por', 'con', 'sin', 'sobre', 'entre',
    'y', 'o', 'pero', 'porque', 'si', 'aunque', 'mientras',
    'ser', 'estar', 'tener', 'hacer', 'decir', 'ir', 'ver',
    'globo', 'rojo', 'azul', 'verde', 'amarillo', 'negro', 'blanco',
    'perro', 'gato', 'casa', 'ciudad', 'paisaje', 'retrato',
    'montaña', 'mar', 'cielo', 'nube', 'sol', 'luna',
    'angel', 'demonio', 'dragon', 'princesa', 'guerrero',
    'jugando', 'corriendo', 'saltando', 'volando', 'caminando',
    'edificio', 'edificios', 'oficina', 'escuela', 'hospital',
    'iglesia', 'tienda', 'calle', 'plaza', 'parque', 'jardín',
    'moderno', 'antiguo', 'nuevo', 'viejo', 'grande', 'pequeño',
    'alto', 'bajo', 'largo', 'corto', 'bonito', 'hermoso'
}

def detectar_idioma(texto: str) -> Tuple[str, float]:
    """Detecta si un texto está en español o inglés"""
    palabras = re.findall(r'\b\w+\b', texto.lower())
    
    if not palabras:
        return ('en', 1.0)
    
    palabras_es = 0
    total = len(palabras)
    
    for p in palabras:
        if p in PALABRAS_ESPANOL:
            palabras_es += 1
    
    if total == 0:
        return ('en', 0.5)
    
    confianza_es = palabras_es / total
    
    if confianza_es > 0.15:
        return ('es', confianza_es)
    else:
        return ('en', 1 - confianza_es)

# ============================================================
# MEJORA DE PROMPT - SOLO TRADUCCIÓN
# ============================================================

def mejorar_prompt(prompt: str) -> str:
    """Solo traduce si es necesario"""
    print(f"   🔄 Prompt original: {prompt}")
    
    idioma, confianza = detectar_idioma(prompt)
    
    print(f"   🏷️ Idioma detectado: {idioma} (confianza: {confianza:.2f})")
    
    if idioma == 'es' and confianza > 0.15:
        print(f"   🌐 Traduciendo al inglés...")
        
        if not _traductor_disponible:
            verificar_traductor()
        
        prompt_traducido = traducir_online(prompt)
        
        if prompt_traducido and prompt_traducido != prompt and len(prompt_traducido) > 2:
            print(f"   🌐 Traducción: {prompt_traducido}")
            prompt_final = prompt_traducido
        else:
            print(f"   ⚠️ Traducción no confiable, usando texto original")
            prompt_final = prompt
    else:
        prompt_final = prompt
        print(f"   🌐 Usando prompt en inglés")
    
    prompt_final = re.sub(r'\s+', ' ', prompt_final)
    
    print(f"   ✨ Prompt final: {prompt_final}")
    
    return prompt_final

# ============================================================
# POST-PROCESAMIENTO DE IMAGEN (MEJORA DE CALIDAD)
# ============================================================

def mejorar_calidad_imagen(imagen: Image.Image) -> Image.Image:
    """
    Aplica mejoras post-procesamiento a la imagen generada
    """
    print("   🔧 Mejorando calidad de imagen...")
    
    try:
        # 1. Aumentar contraste
        enhancer = ImageEnhance.Contrast(imagen)
        imagen = enhancer.enhance(1.15)
        
        # 2. Aumentar nitidez
        enhancer = ImageEnhance.Sharpness(imagen)
        imagen = enhancer.enhance(1.2)
        
        # 3. Aumentar saturación ligeramente
        enhancer = ImageEnhance.Color(imagen)
        imagen = enhancer.enhance(1.1)
        
        # 4. Aumentar brillo ligeramente
        enhancer = ImageEnhance.Brightness(imagen)
        imagen = enhancer.enhance(1.05)
        
        # 5. Filtro de suavizado ligero para reducir ruido
        imagen = imagen.filter(ImageFilter.SMOOTH_MORE)
        
        print("   ✅ Mejoras aplicadas")
        return imagen
        
    except Exception as e:
        print(f"   ⚠️ Error en post-procesamiento: {e}")
        return imagen

# ============================================================
# CARGAR MODELO TINYSD
# ============================================================

_pipe = None
_device = "cpu"

def cargar_modelo():
    """Carga el modelo TinySD"""
    global _pipe
    
    if _pipe is not None:
        return _pipe
    
    print("🎨 Cargando modelo TinySD...")
    print(f"📁 Desde: {MODELO_PATH}")
    
    if not os.path.exists(MODELO_PATH):
        raise FileNotFoundError(f"No se encuentra el modelo en: {MODELO_PATH}")
    
    try:
        _pipe = DiffusionPipeline.from_pretrained(
            MODELO_PATH,
            torch_dtype=torch.float32,
            safety_checker=None,
            requires_safety_checker=False,
            local_files_only=True
        )
        
        _pipe = _pipe.to(_device)
        
        try:
            _pipe.enable_attention_slicing()
        except:
            pass
        
        try:
            _pipe.enable_vae_slicing()
        except:
            pass
        
        print("✅ Modelo TinySD cargado correctamente")
        return _pipe
        
    except Exception as e:
        print(f"❌ Error cargando modelo: {e}")
        raise

# ============================================================
# GENERAR IMAGEN - CALIDAD EXTREMA
# ============================================================

def generar_imagen(
    prompt: str,
    pasos: int = 10,  # MÁXIMO RECOMENDADO
    seed: int = None,
    width: int = 512,  # MÁXIMA RESOLUCIÓN
    height: int = 512,
    guardar: bool = False,
    auto_traducir: bool = True
) -> dict:
    """
    Genera una imagen con CALIDAD EXTREMA
    
    Args:
        prompt: Descripción de la imagen
        pasos: Número de pasos (10 para calidad extrema)
        seed: Semilla para reproducibilidad
        width: Ancho de la imagen (512 máximo)
        height: Alto de la imagen (512 máximo)
        guardar: Si True, guarda en disco
        auto_traducir: Si True, traduce automáticamente
    """
    inicio = time.time()
    
    try:
        if not prompt or len(prompt) < 3:
            return {"success": False, "error": "El prompt debe tener al menos 3 caracteres"}
        
        prompt_final = mejorar_prompt(prompt) if auto_traducir else prompt
        
        pipe = cargar_modelo()
        
        if seed is None:
            seed = int(time.time()) % 1000000
        
        generator = torch.Generator(_device).manual_seed(seed)
        
        print(f"🎨 Generando imagen (CALIDAD EXTREMA)...")
        print(f"   Pasos: {pasos}, Tamaño: {width}x{height}")
        print(f"   Guidance scale: 9.5 (máxima fidelidad)")
        
        # Negative prompt ultra premium para máxima calidad
        negative_prompt = """
        blurry, low quality, distorted, ugly, bad anatomy, worst quality, low resolution, 
        extra limbs, malformed, deformed, watermark, text, signature, out of frame, 
        disfigured, gross proportions, mutation, deformed, cloned face, bad proportions,
        body out of frame, extra fingers, mutated hands, poorly drawn hands, poorly drawn face,
        missing arms, missing legs, extra arms, extra legs, fused fingers, too many fingers,
        long neck, cropped, jpeg artifacts, noisy, oversaturated, undersaturated,
        overexposed, underexposed, grainy, dark, gloomy, blurry background,
        low contrast, washed out, dull, flat, lifeless, amateur, poor quality
        """

        with torch.no_grad():
            resultado = pipe(
                prompt=prompt_final,
                num_inference_steps=pasos,
                generator=generator,
                width=width,
                height=height,
                guidance_scale=9.5,  # MÁXIMA FIDELIDAD
                negative_prompt=negative_prompt
            )
        
        imagen = resultado.images[0]
        
        # ===== POST-PROCESAMIENTO =====
        imagen = mejorar_calidad_imagen(imagen)
        
        # Convertir a base64
        buffer = io.BytesIO()
        imagen.save(buffer, format="PNG", optimize=True)
        img_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        
        nombre = None
        ruta = None
        
        if guardar:
            nombre = f"imagen_{int(time.time())}.png"
            ruta = os.path.join(IMAGENES_PATH, nombre)
            imagen.save(ruta)
            print(f"💾 Imagen guardada en: {ruta}")
        
        tiempo = time.time() - inicio
        
        print(f"✅ Imagen generada en {tiempo:.2f}s")
        
        return {
            "success": True,
            "imagen": img_base64,
            "nombre": nombre,
            "ruta": ruta,
            "tiempo": tiempo,
            "seed": seed,
            "prompt_original": prompt,
            "prompt_traducido": prompt_final,
            "width": width,
            "height": height,
            "pasos": pasos,
            "guardada": guardar
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            "success": False,
            "error": str(e),
            "tiempo": time.time() - inicio,
            "prompt": prompt
        }

# ============================================================
# GUARDAR IMAGEN
# ============================================================

def guardar_imagen(imagen_base64: str, nombre: str = None) -> dict:
    """Guarda una imagen en disco"""
    try:
        if nombre is None:
            nombre = f"imagen_{int(time.time())}.png"
        
        if not nombre.endswith('.png'):
            nombre += '.png'
        
        ruta = os.path.join(IMAGENES_PATH, nombre)
        
        image_data = base64.b64decode(imagen_base64)
        with open(ruta, "wb") as f:
            f.write(image_data)
        
        return {"success": True, "ruta": ruta, "nombre": nombre}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================================
# INICIALIZACIÓN
# ============================================================

print("📚 Inicializando módulo de generación de imágenes...")

try:
    verificar_traductor()
    if _traductor_disponible:
        print("   ✅ Traductor disponible")
    else:
        print("   ⚠️ Traductor no disponible, se usará sin traducción")
except Exception as e:
    print(f"   ⚠️ Error con traductor: {e}")

print("✅ Módulo listo")

# ============================================================
# PRUEBA
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 PROBANDO GENERADOR (CALIDAD EXTREMA)")
    print("=" * 60)
    
    test_prompts = [
        "edificio rojo",
        "globo rojo",
        "paisaje montañoso atardecer",
    ]
    
    for prompt in test_prompts:
        print(f"\n📝 Probando: {prompt}")
        resultado = generar_imagen(
            prompt=prompt,
            pasos=10,
            width=512,
            height=512,
            guardar=False
        )
        
        if resultado.get('success'):
            print(f"   ✅ Tiempo: {resultado.get('tiempo', 0):.2f}s")
        else:
            print(f"   ❌ Error: {resultado.get('error')}")
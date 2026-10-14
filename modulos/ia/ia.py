"""
ia.py - AGENTE IA CON TINYSD (100% LOCAL) - CALIDAD EXTREMA
"""

import os
import sys
import time
import importlib.util
from typing import Dict, Optional, Any, List

# ============================================================
# CONFIGURACIÓN
# ============================================================

class IAConfig:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        self.modelo_path = os.path.join(self.base_dir, "modelo", "tiny-sd")
        self.modulos_path = os.path.join(self.base_dir, "modulos")
        self.imagenes_path = os.path.join(self.base_dir, "modelo", "imagenes")
        
        os.makedirs(self.imagenes_path, exist_ok=True)
        
        print(f"✅ Modelo local: {self.modelo_path}")
        print(f"✅ Imágenes: {self.imagenes_path}")

# ============================================================
# CLASE IA
# ============================================================

class IA:
    def __init__(self, config: Optional[IAConfig] = None):
        self.config = config or IAConfig()
        self.initialized = True
        self.modo = "tinysd_local"
        self.generar_imagen_func = None
        self.guardar_imagen_func = None
        self.generador_cargado = False
        self.modelo_precargado = False
        
        self.historial: List[Dict[str, str]] = []
        self.max_historial = 10
        self.ultima_imagen = None
        self.ultimo_nombre = None
        self.ultimo_seed = None
        
        self.progreso_carga = 0
        self.mensaje_carga = "Iniciando..."
    
    def iniciar(self) -> bool:
        print("=" * 50)
        print("🚀 INICIANDO IA CON TINYSD (LOCAL)")
        print("=" * 50)
        
        if not os.path.exists(self.config.modelo_path):
            print(f"❌ Modelo no encontrado en: {self.config.modelo_path}")
            return False
        
        print("✅ Modelo local encontrado")
        print("✅ IA lista para usar")
        return True
    
    def _cargar_generador(self):
        if self.generador_cargado and self.generar_imagen_func is not None:
            return True
        
        print("🎨 Cargando generador de imágenes local...")
        
        try:
            script_path = os.path.join(self.config.modulos_path, "generar_imagen.py")
            
            if not os.path.exists(script_path):
                print(f"❌ No se encuentra: {script_path}")
                return False
            
            spec = importlib.util.spec_from_file_location("generar_imagen", script_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            self.generar_imagen_func = module.generar_imagen
            self.guardar_imagen_func = module.guardar_imagen if hasattr(module, 'guardar_imagen') else None
            self.generador_cargado = True
            print("✅ Generador local cargado correctamente")
            return True
            
        except Exception as e:
            print(f"❌ Error cargando generador: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def precargar_modelo(self) -> bool:
        if self.modelo_precargado:
            print("✅ Modelo ya estaba precargado")
            return True
        
        print("🔄 Precargando modelo TinySD en memoria...")
        self.progreso_carga = 10
        self.mensaje_carga = "Verificando generador..."
        
        if not self._cargar_generador():
            self.mensaje_carga = "❌ Error cargando generador"
            return False
        
        self.progreso_carga = 30
        self.mensaje_carga = "Generando imagen de prueba..."
        
        try:
            resultado = self.generar_imagen_func(
                prompt="test",
                pasos=4,
                seed=42,
                guardar=False
            )
            
            if resultado.get('success'):
                self.modelo_precargado = True
                self.progreso_carga = 100
                self.mensaje_carga = f"✅ Modelo precargado en {resultado.get('tiempo', 0):.1f}s"
                print(f"✅ Modelo precargado correctamente")
                return True
            else:
                self.progreso_carga = 100
                self.mensaje_carga = f"❌ Error precargando: {resultado.get('error', 'Error desconocido')}"
                return False
                
        except Exception as e:
            self.progreso_carga = 100
            self.mensaje_carga = f"❌ Error precargando: {str(e)}"
            print(f"❌ Error precargando modelo: {e}")
            return False
    
    def enviar_mensaje(self, prompt: str) -> Dict[str, Any]:
        print(f"💬 Chat: {prompt[:100]}...")
        
        respuesta = "Escribe un prompt para generar una imagen en el modo imagen."
        
        self.historial.append({
            "pregunta": prompt,
            "respuesta": respuesta,
            "timestamp": time.time()
        })
        
        if len(self.historial) > self.max_historial:
            self.historial = self.historial[-self.max_historial:]
        
        return {'success': True, 'reply': respuesta, 'tiempo': 0.1}
    
    def generar_imagen(self, prompt: str, guardar: bool = False) -> Dict[str, Any]:
        """Generar imagen con CALIDAD EXTREMA"""
        print(f"🎨 Generando imagen local: {prompt[:100]}...")
        print(f"💾 Guardar en disco: {guardar}")
        
        if not self._cargar_generador():
            return {
                'success': False,
                'error': 'No se pudo cargar el generador local.'
            }
        
        if self.generar_imagen_func is None:
            return {
                'success': False,
                'error': 'Generador no disponible'
            }
        
        try:
            seed = int(time.time()) % 1000000
            
            # CALIDAD EXTREMA: 10 pasos, 512x512, guidance_scale 9.5
            resultado = self.generar_imagen_func(
                prompt=prompt,
                pasos=10,       # Calidad extrema
                seed=seed,
                guardar=guardar,
                width=512,
                height=512
            )
            
            if resultado.get('success'):
                self.ultima_imagen = resultado.get('imagen')
                self.ultimo_nombre = resultado.get('nombre')
                self.ultimo_seed = seed
                self.modelo_precargado = True
                print(f"✅ Imagen generada localmente")
                if guardar:
                    print(f"💾 Guardada en: {resultado.get('ruta')}")
            
            return resultado
            
        except Exception as e:
            print(f"❌ Error generando imagen: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def guardar_imagen_actual(self, nombre: str = None) -> Dict[str, Any]:
        if self.ultima_imagen is None:
            return {
                'success': False,
                'error': 'No hay imagen para guardar.'
            }
        
        if self.guardar_imagen_func is None:
            return {
                'success': False,
                'error': 'Función guardar_imagen no disponible'
            }
        
        try:
            return self.guardar_imagen_func(self.ultima_imagen, nombre)
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def esta_activo(self) -> bool:
        return self.initialized
    
    def obtener_historial(self) -> List[Dict[str, str]]:
        return self.historial.copy()
    
    def obtener_modo(self) -> str:
        return "tinysd_local"
    
    def obtener_estado_carga(self) -> Dict[str, Any]:
        return {
            "precargado": self.modelo_precargado,
            "progreso": self.progreso_carga,
            "mensaje": self.mensaje_carga,
            "generador_cargado": self.generador_cargado
        }
    
    def obtener_ultima_imagen(self) -> Optional[str]:
        return self.ultima_imagen
    
    def limpiar_historial(self):
        self.historial = []
        self.ultima_imagen = None
        self.ultimo_nombre = None
        self.ultimo_seed = None
        print("🧹 Historial limpiado")
    
    def detener(self):
        self.initialized = False
        self.generador_cargado = False
        self.modelo_precargado = False
        print("🛑 IA detenida")
        
        try:
            import gc
            import torch
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            print("🧹 Memoria liberada")
        except:
            pass

# ============================================================
# FUNCIÓN PARA CREAR IA
# ============================================================

def crear_ia(tipo='coder', puerto=8081):
    config = IAConfig()
    return IA(config)

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 PROBANDO IA (CALIDAD EXTREMA)")
    print("=" * 60)
    
    ia = crear_ia()
    ia.iniciar()
    
    print("\n🎨 Generando imagen (calidad extrema)...")
    resultado = ia.generar_imagen("edificio rojo", guardar=False)
    
    if resultado.get('success'):
        print(f"✅ Imagen generada en {resultado.get('tiempo', 0):.1f}s")
        print(f"📝 Prompt usado: {resultado.get('prompt_traducido')}")
        print(f"🔢 Pasos: {resultado.get('pasos')}")
        print(f"📐 Tamaño: {resultado.get('width')}x{resultado.get('height')}")
    else:
        print(f"❌ Error: {resultado.get('error')}")
    
    ia.detener()
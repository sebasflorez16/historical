"""
Script para verificar el contenido del PDF generado
"""

import os
import sys

# Intentar importar PyPDF2 o similar para analizar el PDF
try:
    from PyPDF2 import PdfReader
    tiene_pypdf = True
except ImportError:
    tiene_pypdf = False
    print("⚠️ PyPDF2 no está instalado. Instalando...")
    os.system("pip install PyPDF2")
    try:
        from PyPDF2 import PdfReader
        tiene_pypdf = True
    except:
        tiene_pypdf = False

# Buscar el PDF más reciente
pdf_dir = "/Users/sebasflorez16/Documents/AgroTech Historico/historical/media/informes"
pdfs = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
pdfs.sort(reverse=True)

if not pdfs:
    print("❌ No se encontraron PDFs")
    sys.exit(1)

pdf_path = os.path.join(pdf_dir, pdfs[0])

print("=" * 80)
print("📄 VERIFICACIÓN DEL PDF GENERADO")
print("=" * 80)
print(f"\n📁 Archivo: {pdfs[0]}")
print(f"📊 Tamaño: {os.path.getsize(pdf_path) / (1024*1024):.2f} MB")

if tiene_pypdf:
    try:
        reader = PdfReader(pdf_path)
        print(f"📄 Páginas: {len(reader.pages)}")
        
        # Buscar imágenes en el PDF
        total_images = 0
        for i, page in enumerate(reader.pages):
            if '/XObject' in page['/Resources']:
                xObject = page['/Resources']['/XObject'].get_object()
                for obj in xObject:
                    if xObject[obj]['/Subtype'] == '/Image':
                        total_images += 1
        
        print(f"🖼️  Imágenes totales: {total_images}")
        
        # Extraer texto de las primeras páginas para buscar secciones
        texto_completo = ""
        for i in range(min(10, len(reader.pages))):
            texto_completo += reader.pages[i].extract_text()
        
        # Buscar secciones clave
        secciones = {
            '📊 Resumen Ejecutivo': '📊 Resumen Ejecutivo' in texto_completo,
            '🤖 Análisis Inteligente': 'Análisis Inteligente' in texto_completo or 'Gemini AI' in texto_completo,
            '📸 Galería de Imágenes': 'Galería de Imágenes' in texto_completo,
            '🌱 Análisis NDVI': 'Análisis NDVI' in texto_completo,
            '💧 Análisis NDMI': 'Análisis NDMI' in texto_completo,
        }
        
        print("\n" + "=" * 80)
        print("✅ SECCIONES ENCONTRADAS")
        print("=" * 80)
        for seccion, encontrada in secciones.items():
            estado = "✅" if encontrada else "❌"
            print(f"{estado} {seccion}")
        
        # Buscar referencias espaciales
        referencias_espaciales = [
            'zona norte', 'zona sur', 'zona este', 'zona oeste',
            'norte de la parcela', 'sur de la parcela'
        ]
        
        refs_encontradas = [ref for ref in referencias_espaciales if ref.lower() in texto_completo.lower()]
        
        if refs_encontradas:
            print("\n" + "=" * 80)
            print("🗺️  REFERENCIAS ESPACIALES DETECTADAS")
            print("=" * 80)
            for ref in refs_encontradas:
                print(f"   ✅ '{ref}'")
        
    except Exception as e:
        print(f"\n⚠️ Error analizando PDF: {str(e)}")

else:
    print("\n⚠️ No se puede analizar el contenido del PDF sin PyPDF2")

print("\n" + "=" * 80)
print("💡 PARA ABRIR EL PDF:")
print("=" * 80)
print(f"   open '{pdf_path}'")
print()

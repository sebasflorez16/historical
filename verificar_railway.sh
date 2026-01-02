#!/bin/bash
# Script de verificación pre-deploy para Railway

echo "🔍 VERIFICANDO CONFIGURACIÓN PARA RAILWAY..."
echo "=============================================="
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Verificar archivos necesarios
echo "📁 Verificando archivos necesarios..."

files=("Dockerfile" ".dockerignore" "railway.toml" "requirements.txt" "manage.py")
all_files_ok=true

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅${NC} $file encontrado"
    else
        echo -e "${RED}❌${NC} $file NO encontrado"
        all_files_ok=false
    fi
done

echo ""

# Verificar contenido del Dockerfile
echo "🐳 Verificando Dockerfile..."
if grep -q "gdal-bin" Dockerfile && grep -q "libgdal-dev" Dockerfile; then
    echo -e "${GREEN}✅${NC} Dockerfile contiene dependencias de GDAL"
else
    echo -e "${RED}❌${NC} Dockerfile no contiene dependencias de GDAL"
    all_files_ok=false
fi

echo ""

# Verificar requirements.txt
echo "📦 Verificando requirements.txt..."
if grep -q "GDAL" requirements.txt; then
    echo -e "${GREEN}✅${NC} requirements.txt contiene GDAL"
    gdal_version=$(grep "GDAL==" requirements.txt | cut -d'=' -f3)
    echo "   Versión de GDAL: $gdal_version"
else
    echo -e "${RED}❌${NC} requirements.txt no contiene GDAL"
    all_files_ok=false
fi

if grep -q "gunicorn" requirements.txt; then
    echo -e "${GREEN}✅${NC} requirements.txt contiene gunicorn"
else
    echo -e "${YELLOW}⚠️${NC}  requirements.txt no contiene gunicorn (recomendado)"
fi

if grep -q "whitenoise" requirements.txt; then
    echo -e "${GREEN}✅${NC} requirements.txt contiene whitenoise"
else
    echo -e "${YELLOW}⚠️${NC}  requirements.txt no contiene whitenoise (recomendado)"
fi

echo ""

# Verificar .gitignore
echo "🙈 Verificando .gitignore..."
if [ -f ".gitignore" ]; then
    if grep -q ".env" .gitignore; then
        echo -e "${GREEN}✅${NC} .gitignore protege archivos .env"
    else
        echo -e "${YELLOW}⚠️${NC}  .gitignore no protege archivos .env (agrega *.env)"
    fi
    if grep -q "db.sqlite3" .gitignore; then
        echo -e "${GREEN}✅${NC} .gitignore protege base de datos SQLite"
    else
        echo -e "${YELLOW}⚠️${NC}  .gitignore no protege db.sqlite3"
    fi
else
    echo -e "${YELLOW}⚠️${NC}  Archivo .gitignore no encontrado"
fi

echo ""

# Verificar que no haya archivos sensibles
echo "🔒 Verificando archivos sensibles..."
sensitive_files=(".env" "db.sqlite3" "*.pem" "*.key")
found_sensitive=false

for pattern in "${sensitive_files[@]}"; do
    if ls $pattern 2>/dev/null; then
        echo -e "${RED}❌${NC} Archivo sensible encontrado: $pattern"
        echo "   IMPORTANTE: No subas este archivo a Git"
        found_sensitive=true
    fi
done

if [ "$found_sensitive" = false ]; then
    echo -e "${GREEN}✅${NC} No se encontraron archivos sensibles expuestos"
fi

echo ""

# Verificar estado de Git
echo "🔀 Verificando estado de Git..."
if [ -d ".git" ]; then
    echo -e "${GREEN}✅${NC} Repositorio Git inicializado"
    
    # Verificar branch
    branch=$(git branch --show-current 2>/dev/null)
    echo "   Branch actual: $branch"
    
    # Verificar si hay cambios sin commit
    if git status --porcelain | grep -q "^"; then
        echo -e "${YELLOW}⚠️${NC}  Hay cambios sin commit"
        echo "   Ejecuta: git add . && git commit -m 'Preparar para Railway'"
    else
        echo -e "${GREEN}✅${NC} No hay cambios pendientes"
    fi
    
    # Verificar remote
    if git remote -v | grep -q "origin"; then
        echo -e "${GREEN}✅${NC} Remote 'origin' configurado"
        git remote -v | head -1
    else
        echo -e "${YELLOW}⚠️${NC}  No hay remote configurado"
        echo "   Ejecuta: git remote add origin https://github.com/TU_USUARIO/agrotech-historico.git"
    fi
else
    echo -e "${RED}❌${NC} No es un repositorio Git"
    echo "   Ejecuta: git init"
    all_files_ok=false
fi

echo ""
echo "=============================================="

if [ "$all_files_ok" = true ]; then
    echo -e "${GREEN}✅ TODO LISTO PARA DESPLEGAR EN RAILWAY${NC}"
    echo ""
    echo "Próximos pasos:"
    echo "1. git add ."
    echo "2. git commit -m 'Configurar para Railway'"
    echo "3. git push origin main"
    echo "4. Crear proyecto en railway.app"
    echo ""
else
    echo -e "${RED}❌ HAY PROBLEMAS QUE RESOLVER ANTES DE DESPLEGAR${NC}"
    echo ""
    echo "Revisa los errores marcados arriba y corrígelos."
    echo ""
fi

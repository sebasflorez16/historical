#!/usr/bin/env python
"""
Script para crear un superusuario en Railway de forma no interactiva
Uso: railway run python create_superuser.py
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'agrotech_historico.settings_production')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# Configuración del superusuario
username = os.getenv('DJANGO_SUPERUSER_USERNAME', 'admin')
email = os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@agrotech.com')
password = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'admin123')

# Verificar si el usuario ya existe
if User.objects.filter(username=username).exists():
    print(f"❌ El usuario '{username}' ya existe.")
    user = User.objects.get(username=username)
    print(f"✅ Usuario encontrado: {user.username} ({user.email})")
else:
    # Crear superusuario
    user = User.objects.create_superuser(
        username=username,
        email=email,
        password=password
    )
    print(f"✅ Superusuario creado exitosamente!")
    print(f"   Username: {username}")
    print(f"   Email: {email}")
    print(f"   Password: {password}")
    print(f"\n🔐 Accede al admin en: https://historical-production.up.railway.app/admin/")

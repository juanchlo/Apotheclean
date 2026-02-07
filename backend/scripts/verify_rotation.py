import requests
import uuid
import sys

BASE_URL = "http://localhost:5000/api/auth"

def run_verification():
    print("Iniciando verificación de rotación de tokens...")
    
    # 1. Registrar usuario
    username = f"user_{uuid.uuid4().hex[:8]}"
    email = f"{username}@test.com"
    password = "password123"
    
    print(f"1. Registrando usuario: {username}")
    resp_reg = requests.post(f"{BASE_URL}/registro", json={
        "username": username,
        "email": email,
        "password": password,
        "nombre": "Test User"
    })
    
    if resp_reg.status_code != 201:
        print(f"Error registrando usuario: {resp_reg.text}")
        sys.exit(1)
        
    print("   -> Registro exitoso")

    # 2. Login
    print("2. Iniciando sesión...")
    resp_login = requests.post(f"{BASE_URL}/login", json={
        "username": username,
        "password": password
    })
    
    if resp_login.status_code != 200:
        print(f"Error en login: {resp_login.text}")
        sys.exit(1)
        
    data = resp_login.json()
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]
    print(f"   -> Login exitoso. Refresh Token: {refresh_token[:10]}...")

    # 3. Refresh (Rotación)
    print("3. Probando renovación de tokens...")
    resp_refresh = requests.post(f"{BASE_URL}/refresh", json={
        "refresh_token": refresh_token
    })
    
    if resp_refresh.status_code != 200:
        print(f"Error en refresh: {resp_refresh.text}")
        sys.exit(1)
        
    new_data = resp_refresh.json()
    new_access_token = new_data["access_token"]
    new_refresh_token = new_data["refresh_token"]
    
    print(f"   -> Refresh exitoso. Nuevo Refresh Token: {new_refresh_token[:10]}...")
    
    if refresh_token == new_refresh_token:
        print("ERROR: El refresh token NO cambió. La rotación no está funcionando.")
        sys.exit(1)
    else:
        print("   -> ¡CORRECTO! El refresh token ha rotado.")

    # 4. Validar invalidación del token anterior
    print("4. Verificando invalidación del token anterior...")
    resp_old_refresh = requests.post(f"{BASE_URL}/refresh", json={
        "refresh_token": refresh_token
    })
    
    if resp_old_refresh.status_code in [400, 401]:
        print(f"   -> ¡CORRECTO! El token anterior fue rechazado ({resp_old_refresh.status_code}).")
    else:
        print(f"ERROR: El token anterior SIGUE siendo válido. Status: {resp_old_refresh.status_code}")
        print(resp_old_refresh.text)
        sys.exit(1)

    print("\nVERIFICACIÓN COMPLETADA EXITOSAMENTE")

if __name__ == "__main__":
    try:
        run_verification()
    except requests.exceptions.ConnectionError:
        print("ERROR: No se pudo conectar a localhost:5000. Asegúrate de que el backend esté corriendo.")
        sys.exit(1)

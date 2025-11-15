import json
import bcrypt

USERS_FILE = "users_example.json"

def add_user(username: str, password: str, language: str = "es"):
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            users = json.load(f)
    except FileNotFoundError:
        users = {}

    if isinstance(users, dict) and "usuarios" in users:
        flat = {}
        for u in users["usuarios"]:
            flat[u.get("username")] = {"password": u.get("password"), "language": u.get("language","es")}
        users = flat

    if username in users:
        print("⚠️ El usuario ya existe.")
        return

    hashed_pw = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    users[username] = {"password": hashed_pw, "language": language}

    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

    print(f"✅ Usuario '{username}' agregado correctamente.")

if __name__ == "__main__":
    print("👤 Crear nuevo usuario para FinanzApp")
    username = input("Nombre de usuario: ").strip()
    password = input("Contraseña: ").strip()
    language = input("Idioma (es/en): ").strip().lower() or "es"
    add_user(username, password, language)

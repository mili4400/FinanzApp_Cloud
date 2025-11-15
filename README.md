# FinanzApp

Versión lista para Streamlit Cloud: autenticación local, tema oscuro, selector de idioma y funciones de análisis.

Repositorio sugerido: https://github.com/mili4400/FinanzApp_JSON_Cloud

## Archivos principales
- `app_finanzapp.py` - App principal (completa)
- `create_user.py` - Script para crear usuarios con bcrypt
- `users_example.json` - Usuarios de ejemplo (hashed passwords)
- `requirements.txt` - Dependencias
- `assets/` - Imágenes de preview

## Ejecutar localmente (opcional)
```bash
pip install -r requirements.txt
streamlit run app_finanzapp.py
```

## Añadir usuario local
```bash
python create_user.py
```

## Deploy en Streamlit Cloud
1. Subí el repo a GitHub: https://github.com/mili4400/FinanzApp_JSON_Cloud
2. En Streamlit Cloud → New app → seleccioná el repo
3. Main file path: `app_finanzapp.py`
4. En Settings → Secrets añadí:
```
EODHD_API_KEY = tu_api_key_aqui
```
5. Deploy 🚀

FinanzApp — powered by EODHD

# 📊 Análisis de Portafolio

Herramienta web para analizar y medir el rendimiento de una cartera de inversión.
Desarrollada con **Python + Streamlit**, diseñada para inversores que necesitan métricas detalladas, seguimiento histórico y análisis de transacciones.

---

## 🚀 Funcionalidades

- **Vista actual del portafolio**: holdings, valor de mercado, capital invertido, ganancias/pérdidas
- **Evolución histórica**: rendimiento en rangos de fechas personalizados
- **Análisis de transacciones**: compras, ventas, dividendos, cupones, amortizaciones
- **Soporte multi-activo**: acciones, bonos y otros instrumentos financieros
- **Exportación a CSV**

### Próximamente
- 📈 Gráficos interactivos con Plotly
- 🗂️ Dashboard multi-página
- 📅 Timeline de evolución visual

---

## 📁 Estructura del Proyecto

```
analisis-de-portafolio/
├── app.py                  # Aplicación principal Streamlit
├── requirements.txt        # Dependencias Python
├── .gitignore
├── README.md
│
├── data/                   # Archivos de datos
│   └── ejemplo_cartera.xlsx  # Archivo de ejemplo con formato correcto
│
├── modules/                # Módulos de lógica de negocio
│   ├── __init__.py
│   ├── portafolio.py       # Cálculo de posiciones actuales
│   ├── evolucion.py        # Análisis de evolución histórica
│   └── operaciones.py      # Procesamiento de transacciones
│
├── utils/                  # Utilidades generales
│   ├── __init__.py
│   ├── cargador.py         # Carga y validación de archivos Excel
│   └── exportador.py       # Exportación de resultados (CSV, etc.)
│
└── assets/                 # Recursos estáticos (imágenes, estilos)
```

---

## 📋 Formato del Archivo Excel

El archivo Excel debe contener **dos hojas**:

### Hoja `Operaciones`
| Fecha | Tipo Operacion | Categoria | Activo | Cantidad Nominal | Precio | Valor |
|-------|---------------|-----------|--------|-----------------|--------|-------|
| ...   | Compra/Venta/Dividendo/Cupon/Amortizacion | Accion/Bono | AAPL | 100 | 150.00 | 15000.00 |

### Hoja `Precios`
Precios de cierre diarios por activo, con fechas en filas y símbolos en columnas.

---

## ⚙️ Instalación

```bash
# 1. Clonar el repositorio
git clone https://github.com/santyago-pixel/analisis-de-portafolio.git
cd analisis-de-portafolio

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar la app
streamlit run app.py
```

---

## 📂 Uso

1. Ejecutar la app con `streamlit run app.py`
2. Cargar tu archivo Excel desde la interfaz (o usar el archivo de ejemplo)
3. Explorar las secciones: **Portafolio Actual** y **Evolución Histórica**
4. Exportar resultados en CSV si es necesario

---

## 🛠️ Tecnologías

| Tecnología | Uso |
|-----------|-----|
| Python 3.8+ | Lenguaje principal |
| Streamlit | Interfaz web |
| Pandas | Procesamiento de datos |
| OpenPyXL | Lectura de archivos Excel |

---

## 📄 Licencia

MIT License — libre para usar y modificar.

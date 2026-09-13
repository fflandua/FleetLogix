# FleetLogix

Proyecto de Data Analytics orientado a la construcción de una infraestructura de datos para una empresa de logística y transporte.

Esta etapa implementa una base de datos relacional en PostgreSQL, un proceso automatizado de generación y carga de datos sintéticos en Python y controles SQL para validar la calidad e integridad de los datos.

## Stack tecnológico

- **PostgreSQL 15+**: sistema de gestión de base de datos relacional.
- **Python 3.10+**: generación y carga automatizada de datos.
- **DBeaver**: administración y consulta de PostgreSQL.
- **Faker**: generación de datos sintéticos.
- **pandas / NumPy**: procesamiento y generación de datos.
- **psycopg2**: conexión entre Python y PostgreSQL.
- **Jupyter Notebook**: entorno de análisis y desarrollo.
- **Git / GitHub**: control de versiones y publicación del proyecto.

## Estructura del repositorio

```text
FleetLogix/
├── docs/
│   ├── README.pdf
│   └── diagrama_er_fleetlogix.png
│
├── python/
│   └── A1-01_data_generation_estudiantes.py
│
├── sql/
│   ├── fleetlogix_db_schema.sql
│   └── validacion_calidad_datos.sql
│
└── README.md
```

## Modelo de datos

El modelo relacional está compuesto por seis tablas:

`vehicles` · `drivers` · `routes` · `trips` · `deliveries` · `maintenance`

La estructura de la base de datos, incluyendo tablas, claves primarias, claves foráneas, constraints e índices, se encuentra definida en:

[`sql/fleetlogix_db_schema.sql`](sql/fleetlogix_db_schema.sql)

El modelo establece cinco relaciones principales:

- `vehicles` → `trips`
- `drivers` → `trips`
- `routes` → `trips`
- `trips` → `deliveries`
- `vehicles` → `maintenance`

El diagrama entidad-relación puede consultarse en:

[`docs/diagrama_er_fleetlogix.png`](docs/diagrama_er_fleetlogix.png)

La documentación completa del modelo y del desarrollo del proyecto se encuentra en:

[`docs/README.pdf`](docs/README.pdf)

## Generación de datos sintéticos

La generación y carga automatizada se realiza mediante:

[`python/A1-01_data_generation_estudiantes.py`](python/A1-01_data_generation_estudiantes.py)

El generador construye los datos respetando las dependencias entre las entidades del modelo para mantener coherencia entre los registros.

Entre las principales reglas implementadas se encuentran:

- utilización de vehículos y conductores activos para generar viajes;
- asignación de rutas existentes;
- distribución de 100.000 viajes a lo largo de aproximadamente dos años;
- distribución horaria no uniforme para representar diferentes niveles de actividad;
- peso transportado limitado por la capacidad del vehículo;
- generación de entre 2 y 6 entregas por viaje, siendo 4 la cantidad más probable;
- entregas vinculadas a viajes existentes;
- distribución del peso de los paquetes en función del peso transportado;
- mantenimientos generados a partir del historial de viajes de cada vehículo.

### Resultado de la generación

| Tabla | Registros |
|---|---:|
| `vehicles` | 200 |
| `drivers` | 400 |
| `routes` | 50 |
| `trips` | 100.000 |
| `deliveries` | 400.000 |
| `maintenance` | 4.913 |
| **Total** | **505.563** |

## Control de calidad

Las validaciones posteriores a la generación y carga se encuentran en:

[`sql/validacion_calidad_datos.sql`](sql/validacion_calidad_datos.sql)

El script realiza tres grupos de controles:

### Volumen de datos

Verifica la cantidad de registros almacenados en cada una de las seis tablas.

### Integridad referencial

Comprueba las cinco relaciones del modelo para detectar posibles registros sin correspondencia:

- `trips.vehicle_id` → `vehicles.vehicle_id`
- `trips.driver_id` → `drivers.driver_id`
- `trips.route_id` → `routes.route_id`
- `deliveries.trip_id` → `trips.trip_id`
- `maintenance.vehicle_id` → `vehicles.vehicle_id`

Las validaciones realizadas no detectaron registros con referencias inválidas.

### Consistencia temporal

Verifica que la fecha y hora de llegada de cada viaje sea posterior a su fecha y hora de salida.

Las validaciones realizadas no detectaron viajes con fechas inconsistentes.

## Instalación y ejecución

### 1. Requisitos

- PostgreSQL 15+
- Python 3.10+
- DBeaver o cliente compatible con PostgreSQL

### 2. Crear la base de datos

Crear una base PostgreSQL llamada:

```text
fleetlogix
```

### 3. Crear el modelo relacional

Ejecutar sobre la base `fleetlogix`:

[`sql/fleetlogix_db_schema.sql`](sql/fleetlogix_db_schema.sql)

Este script crea las seis tablas y sus relaciones.

### 4. Instalar las dependencias de Python

```bash
pip install psycopg2-binary pandas numpy faker tabulate jupyter notebook
```

### 5. Configurar la conexión

Configurar los parámetros de conexión a PostgreSQL utilizados por:

[`python/A1-01_data_generation_estudiantes.py`](python/A1-01_data_generation_estudiantes.py)

> Las credenciales de acceso a PostgreSQL no deben publicarse en el repositorio.

### 6. Generar y cargar los datos

Desde la raíz del proyecto:

```bash
python python/A1-01_data_generation_estudiantes.py
```

El script genera los datos sintéticos y los carga en PostgreSQL respetando las relaciones del modelo.

### 7. Ejecutar los controles de calidad

Una vez finalizada la carga, ejecutar:

[`sql/validacion_calidad_datos.sql`](sql/validacion_calidad_datos.sql)

El script permite verificar los volúmenes generados, la integridad referencial y la consistencia temporal de los viajes.

## Documentación

La documentación completa del proyecto se encuentra disponible en:

[`docs/README.pdf`](docs/README.pdf)

Incluye el análisis del modelo relacional, diagrama ER, descripción de tablas y constraints, patrones de negocio, generación de datos sintéticos, ajustes realizados, controles de calidad y mejoras identificadas.

## Mejoras futuras

Entre las principales mejoras técnicas identificadas se encuentran:

- incorporar el tipo de licencia del conductor y validar su compatibilidad con los vehículos;
- controlar la disponibilidad de conductores para evitar viajes con horarios superpuestos;
- refinar el cálculo del consumo de combustible según vehículo, distancia y carga;
- mejorar la simulación de entregas demoradas;
- ampliar las validaciones automáticas del proceso de generación;
- incorporar nuevas variables operativas que permitan realizar análisis de costos, rentabilidad, utilización de vehículos y mantenimiento preventivo.
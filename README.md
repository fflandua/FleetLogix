# FleetLogix

Proyecto de Data Analytics orientado a la construcción de una infraestructura de datos para una empresa de logística y transporte.

El proyecto implementa una base de datos relacional en PostgreSQL, procesos de generación y validación de datos sintéticos, análisis y optimización mediante SQL y un Data Warehouse en Snowflake alimentado mediante procesos ETL desarrollados en Python.

## Stack tecnológico

- **PostgreSQL 15+**: sistema de gestión de la base de datos operacional.
- **Python 3.10+**: generación, procesamiento y carga de datos.
- **Snowflake**: Data Warehouse y entorno analítico.
- **DBeaver**: administración y consulta de PostgreSQL y Snowflake.
- **Faker**: generación de datos sintéticos.
- **pandas / NumPy**: procesamiento y transformación de datos.
- **psycopg2**: conexión entre Python y PostgreSQL.
- **Snowflake Connector for Python**: conexión entre Python y Snowflake.
- **Git / GitHub**: control de versiones y publicación del proyecto.

## Estructura del repositorio

```text
FleetLogix/

├── docs/
│   ├── README.pdf
│   ├── Manual_Consultas_SQL.pdf
│   └── diagrama_er_fleetlogix.png
│
├── python/
│   ├── A1-01_data_generation_estudiantes.py
│   ├── A3-05_etl_pipeline_estudiantes.py
│   └── initial_load.py
│
├── scripts/
│   ├── 02_queries_analysis.sql
│   ├── 03_optimization_indexes.sql
│   ├── A3-04_dimensional_model.sql
│   ├── fleetlogix_db_schema.sql
│   └── validacion_calidad_datos.sql
│
└── README.md
```

## Modelo de datos

El modelo relacional está compuesto por seis tablas:

`vehicles` · `drivers` · `routes` · `trips` · `deliveries` · `maintenance`

La estructura de la base de datos, incluyendo tablas, claves primarias, claves foráneas, constraints e índices, se encuentra definida en:

[`scripts/fleetlogix_db_schema.sql`](scripts/fleetlogix_db_schema.sql)

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

[`scripts/validacion_calidad_datos.sql`](scripts/validacion_calidad_datos.sql)

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

## Análisis y optimización SQL

El segundo avance utiliza la base operacional generada para obtener información sobre el desempeño de FleetLogix mediante consultas SQL de diferentes niveles de complejidad.

Las consultas utilizadas para el análisis se encuentran en:

[`scripts/02_queries_analysis.sql`](scripts/02_queries_analysis.sql)

Durante esta etapa se analizaron consultas relacionadas con la composición de la flota, vencimiento de licencias, estado de los viajes, distribución de entregas, actividad de los conductores, consumo de combustible, retrasos y costos de mantenimiento.

También se utilizó `EXPLAIN ANALYZE` para estudiar los planes de ejecución y establecer tiempos de referencia antes de aplicar las optimizaciones.

### Optimización mediante índices

Los índices utilizados para optimizar las consultas se encuentran definidos en:

[`scripts/03_optimization_indexes.sql`](scripts/03_optimization_indexes.sql)

Se implementaron cinco índices orientados a mejorar operaciones relacionadas con viajes, entregas, conductores, rutas y mantenimientos.

Posteriormente se compararon los tiempos de ejecución antes y después de la implementación para evaluar el impacto de las optimizaciones.

El análisis detallado de las consultas se encuentra documentado en:

[`docs/Manual_Consultas_SQL.pdf`](docs/Manual_Consultas_SQL.pdf)

## Data Warehouse en Snowflake

El tercer avance incorpora una capa analítica separada de la base operacional mediante la implementación de un Data Warehouse en Snowflake.

El modelo dimensional se encuentra definido en:

[`scripts/A3-04_dimensional_model.sql`](scripts/A3-04_dimensional_model.sql)

Se implementó la base `FLEETLOGIX_DW` y el esquema `ANALYTICS` utilizando un esquema estrella cuya tabla central es `FACT_DELIVERIES`.

La tabla de hechos se relaciona con seis dimensiones:

- `DIM_DATE`
- `DIM_TIME`
- `DIM_VEHICLE`
- `DIM_DRIVER`
- `DIM_ROUTE`
- `DIM_CUSTOMER`

El entorno también incorpora Time Travel de 30 días, vistas seguras y roles para controlar el acceso a la información.

### Carga inicial

Para poblar el Data Warehouse con los datos históricos existentes en PostgreSQL se desarrolló:

[`python/initial_load.py`](python/initial_load.py)

Este proceso realiza la carga inicial de las dimensiones y posteriormente incorpora las entregas completadas en `FACT_DELIVERIES`.

La carga validada en Snowflake produjo:

| Tabla | Registros |
|---|---:|
| `DIM_DATE` | 731 |
| `DIM_TIME` | 24 |
| `DIM_VEHICLE` | 200 |
| `DIM_DRIVER` | 400 |
| `DIM_ROUTE` | 50 |
| `DIM_CUSTOMER` | 341.378 |
| `FACT_DELIVERIES` | 397.882 |

### Pipeline ETL diario

Las nuevas entregas se incorporan al Data Warehouse mediante:

[`python/A3-05_etl_pipeline_estudiantes.py`](python/A3-05_etl_pipeline_estudiantes.py)

El pipeline realiza las etapas de extracción, transformación y carga entre PostgreSQL y Snowflake.

Entre sus principales funciones se encuentran:

- extracción de las entregas correspondientes al día anterior;
- cálculo de métricas de tiempo, retraso, eficiencia, costo e ingreso;
- aplicación de controles de calidad;
- actualización de dimensiones;
- tratamiento de cambios históricos en conductores mediante SCD Tipo 2;
- carga de las entregas en `FACT_DELIVERIES`;
- identificación de cada ejecución mediante `etl_batch_id`;
- precálculo de totales en `DAILY_TOTALS`.

El proceso queda programado para ejecutarse diariamente a las **02:00**.

## Instalación y ejecución

### 1. Requisitos

- PostgreSQL 15+
- Python 3.10+
- DBeaver o cliente compatible
- Cuenta de Snowflake para la ejecución del Data Warehouse y el pipeline ETL

### 2. Crear la base de datos operacional

Crear una base PostgreSQL llamada:

```text
fleetlogix
```

### 3. Crear el modelo relacional

Ejecutar sobre la base `fleetlogix`:

[`scripts/fleetlogix_db_schema.sql`](scripts/fleetlogix_db_schema.sql)

Este script crea las seis tablas y sus relaciones.

### 4. Instalar las dependencias de Python

```bash
pip install psycopg2-binary pandas numpy faker tabulate snowflake-connector-python schedule
```

### 5. Configurar las conexiones

Configurar los parámetros de conexión necesarios para PostgreSQL y Snowflake en los scripts correspondientes.

> Las credenciales de acceso a PostgreSQL y Snowflake no deben publicarse en el repositorio.

### 6. Generar y cargar los datos operacionales

Desde la raíz del proyecto:

```bash
python python/A1-01_data_generation_estudiantes.py
```

### 7. Ejecutar los controles de calidad

Una vez finalizada la carga operacional, ejecutar:

[`scripts/validacion_calidad_datos.sql`](scripts/validacion_calidad_datos.sql)

### 8. Implementar el Data Warehouse

Ejecutar en Snowflake:

[`scripts/A3-04_dimensional_model.sql`](scripts/A3-04_dimensional_model.sql)

### 9. Realizar la carga histórica inicial

```bash
python python/initial_load.py
```

La carga inicial se utiliza para poblar el Data Warehouse con los datos históricos existentes en PostgreSQL.

### 10. Ejecutar el pipeline ETL

```bash
python python/A3-05_etl_pipeline_estudiantes.py
```

El pipeline queda activo y programado para ejecutar el proceso ETL diariamente a las 02:00.

## Documentación

La documentación completa del proyecto se encuentra disponible en:

[`docs/README.pdf`](docs/README.pdf)

El documento reúne el desarrollo de los tres avances realizados: implementación y validación de la base operacional, análisis y optimización SQL, construcción del Data Warehouse en Snowflake y desarrollo del pipeline ETL.

El detalle de las consultas SQL se encuentra disponible en:

[`docs/Manual_Consultas_SQL.pdf`](docs/Manual_Consultas_SQL.pdf)

## Mejoras futuras

Entre las mejoras identificadas durante el desarrollo se encuentran:

- ampliar los controles de calidad de los datos;
- optimizar los procesos de carga para mayores volúmenes de información;
- incorporar controles para evitar cargas duplicadas en el Data Warehouse;
- ampliar el registro y seguimiento de las ejecuciones del pipeline;
- continuar incorporando métricas que permitan analizar costos, rentabilidad y eficiencia operacional.
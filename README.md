# FleetLogix

Proyecto integrador de Data Analytics orientado al análisis y gestión de datos de una empresa de logística y transporte.

El proyecto utiliza una base de datos relacional en PostgreSQL para representar la operación de FleetLogix, incluyendo vehículos, conductores, rutas, viajes, entregas y mantenimientos.

## Objetivo del proyecto

Construir una solución de datos que permita almacenar, validar y analizar información relacionada con las operaciones logísticas de FleetLogix.

En esta primera etapa se desarrolla el modelo relacional, la generación de datos sintéticos y los controles de calidad necesarios para garantizar la coherencia e integridad de los datos.

## Tecnologías utilizadas

- **PostgreSQL**: sistema de gestión de base de datos relacional.
- **DBeaver**: administración de la base de datos y ejecución de consultas SQL.
- **Python**: generación y carga automatizada de datos sintéticos.
- **Faker**: generación de datos ficticios realistas.
- **pandas**: herramienta para manipulación y procesamiento de datos.
- **NumPy**: generación de valores y distribuciones probabilísticas.
- **psycopg2**: conexión entre Python y PostgreSQL.
- **tqdm**: visualización del progreso durante la generación masiva de datos.
- **Visual Studio Code**: desarrollo y organización de los archivos del proyecto.
- **Git y GitHub**: control de versiones y almacenamiento del repositorio.

## Instalación y ejecución

### Requisitos

Para ejecutar el proyecto se requiere:

- Python 3
- PostgreSQL
- Una base de datos creada para FleetLogix

### Dependencias de Python

Instalar las librerías utilizadas por el generador:

```bash
pip install pandas numpy faker psycopg2-binary tqdm
```

### Configuración de la base de datos

Antes de ejecutar el generador, configurar los datos de conexión a PostgreSQL en `DB_CONFIG`:

```python
DB_CONFIG = {
    'host': 'localhost',
    'database': 'Fleetlogix',
    'user': 'postgres',
    'password': 'TU_PASSWORD',
    'port': '5432'
}
```

> La contraseña debe reemplazarse por la correspondiente al entorno local y no debe publicarse en el repositorio.

### Ejecución

Una vez creada la estructura de la base de datos y configurada la conexión, ejecutar el generador desde la carpeta `python`:

```bash
cd python
python A1-01_data_generation_estudiantes.py
```

Al finalizar, el script muestra un resumen con la cantidad de registros generados y los resultados de las validaciones incorporadas al proceso.

Las validaciones adicionales sobre la base cargada pueden ejecutarse mediante:

`sql/validacion_calidad_datos.sql`

## Estructura del proyecto

El proyecto se organiza en diferentes carpetas según la función de cada archivo:

```text
FleetLogix/
├── docs/
│   ├── modelo_relacional.md
│   └── diagrama_er_fleetlogix.png
├── python/
│   └── A1-01_data_generation_estudiantes.py
├── sql/
│   └── validacion_calidad_datos.sql
└── README.md
```

- **docs/**: documentación del modelo relacional y diagrama entidad-relación.
- **python/**: script utilizado para la generación y carga de datos sintéticos.
- **sql/**: consultas utilizadas para validar la calidad e integridad de los datos.

## Generación de datos sintéticos

La generación de datos fue diseñada para simular una operación logística coherente. Los valores no se generan de forma completamente independiente: cada tabla utiliza información de las tablas relacionadas para construir registros consistentes.

### Lógica de generación

**Vehículos**

La flota se genera utilizando cuatro tipos de vehículos: Camión Grande, Camión Mediano, Van y Motocicleta. Cada vehículo posee características operativas como capacidad de carga, tipo de combustible, fecha de adquisición y estado.

**Conductores**

Los conductores se generan con datos personales ficticios, código de empleado, número de licencia, fecha de vencimiento, fecha de contratación y estado. Para la asignación de viajes se utilizan conductores activos cuya licencia se encuentre vigente.

**Rutas**

Las rutas conectan cinco ciudades principales. Cada ruta contiene una ciudad de origen y destino, distancia, duración estimada y costo de peajes. Estos valores posteriormente son utilizados para generar las características de los viajes.

**Viajes**

Los viajes se distribuyen a lo largo de dos años de operación histórica.

La hora de salida no se elige con una distribución uniforme. El generador asigna diferentes probabilidades a las 24 horas del día para representar períodos con mayor y menor actividad logística.

Cada viaje utiliza un vehículo, un conductor y una ruta existentes. A partir de estos datos se generan otras variables relacionadas:

- La duración del viaje toma como referencia la duración estimada de la ruta.
- La fecha y hora de llegada se calcula a partir de la salida y la duración del viaje, garantizando que la llegada sea posterior a la salida.
- El consumo de combustible se calcula en función de la distancia recorrida.
- El peso transportado se genera entre el 40% y el 90% de la capacidad del vehículo, evitando superar su capacidad máxima.

**Entregas**

Cada entrega pertenece a un viaje existente. La cantidad de entregas por viaje se genera entre 2 y 6, siendo 4 la cantidad más probable.

El peso de los paquetes no se genera independientemente del viaje. El generador distribuye aproximadamente el 95% del peso transportado entre sus entregas, dejando un margen para elementos operativos como embalajes, pallets u otros componentes de carga.

Las fechas programadas y efectivas de entrega también se generan en relación con el viaje, permitiendo posteriormente analizar cumplimiento y retrasos.

**Mantenimiento**

Los registros de mantenimiento se generan a partir del historial de viajes de cada vehículo, utilizando como referencia aproximadamente un mantenimiento cada 20 viajes.

Los tipos de mantenimiento incluyen cambio de aceite, revisión de frenos, cambio de llantas, mantenimiento general, revisión de motor y alineación y balanceo.

### Resultado de la generación

| Tabla | Registros |
|---|---:|
| vehicles | 200 |
| drivers | 400 |
| routes | 48 |
| trips | 100000 |
| deliveries | 400000 |
| maintenance | 4920 |
| **Total** | **505568** |

## Control de calidad de datos

Una vez finalizada la carga, se realizan controles sobre la base de datos para verificar que los registros generados mantengan las reglas definidas por el modelo.

Las validaciones SQL se encuentran en `sql/validacion_calidad_datos.sql`.

### Integridad referencial

Se verifica la existencia de registros huérfanos en las cinco relaciones del modelo:

- `trips.vehicle_id` → `vehicles.vehicle_id`
- `trips.driver_id` → `drivers.driver_id`
- `trips.route_id` → `routes.route_id`
- `deliveries.trip_id` → `trips.trip_id`
- `maintenance.vehicle_id` → `vehicles.vehicle_id`

La validación sobre los datos generados no detectó registros huérfanos.

### Consistencia temporal

Se controla que la fecha y hora de llegada de cada viaje sea siempre posterior a su fecha y hora de salida:

`arrival_datetime > departure_datetime`

La validación no detectó viajes con fechas inconsistentes.

### Control de carga

El proceso de generación registra mediante logs las distintas etapas de ejecución, incluyendo conexión a PostgreSQL, generación de registros, progreso de inserción, validaciones, errores y cierre de la conexión.

## Documentación

La documentación técnica del proyecto se encuentra en la carpeta `docs/`:

- `modelo_relacional.md`: descripción de tablas, relaciones y constraints del modelo.
- `diagrama_er_fleetlogix.png`: representación visual del modelo entidad-relación.

El proyecto también incluye `sql/validacion_calidad_datos.sql`, utilizado para verificar los volúmenes cargados, la integridad referencial y la consistencia temporal de los datos.

## Mejoras futuras

El modelo actual permite representar la operación básica de FleetLogix y constituye una base para futuros análisis. A partir de su estructura y de los datos generados se identifican oportunidades de mejora tanto técnicas como de negocio.

### Mejoras del modelo y generación de datos

- Incorporar el tipo de licencia del conductor y definir su compatibilidad con los distintos tipos de vehículos.
- Refinar el cálculo del consumo de combustible considerando el tipo de vehículo, la distancia recorrida y la carga transportada.
- Mejorar la lógica de entregas demoradas para representar con mayor precisión el cumplimiento de los horarios programados.
- Ampliar las validaciones automáticas del script Python para cubrir todas las relaciones del modelo.
- Revisar los parámetros de generación de rutas y mantenimientos para permitir un mayor control sobre los volúmenes generados.

### Mejoras orientadas al negocio

- Incorporar información sobre costos operativos de cada viaje para analizar la rentabilidad de rutas y operaciones.
- Registrar tarifas o ingresos asociados a las entregas para comparar ingresos y costos.
- Incorporar información geográfica más detallada que permita analizar recorridos, zonas de entrega y eficiencia de las rutas.
- Registrar causas de retrasos y entregas fallidas para identificar problemas recurrentes en la operación.
- Incorporar métricas de utilización de los vehículos para detectar unidades con baja utilización o sobrecarga operativa.
- Analizar el historial de mantenimiento junto con kilometraje, viajes realizados y costos para avanzar hacia estrategias de mantenimiento preventivo.
- Incorporar indicadores de desempeño de conductores, rutas y vehículos que permitan comparar eficiencia, cumplimiento y costos.
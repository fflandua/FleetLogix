import os
import psycopg2
import snowflake.connector
import pandas as pd


# ==========================================
# CONFIGURACIÓN DE CONEXIONES
# ==========================================

# Datos de conexión a PostgreSQL
POSTGRES_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB', 'fleetlogix'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD')
}

# Datos de conexión a Snowflake
SNOWFLAKE_CONFIG = {
    'account': os.getenv('SNOWFLAKE_ACCOUNT'),
    'user': os.getenv('SNOWFLAKE_USER'),
    'password': os.getenv('SNOWFLAKE_PASSWORD'),
    'warehouse': 'FLEETLOGIX_WH',
    'database': 'FLEETLOGIX_DW',
    'schema': 'ANALYTICS'
}


# ==========================================
# CONEXIÓN A LAS BASES DE DATOS
# ==========================================

def connect_databases():
    """Conectar a PostgreSQL y Snowflake"""
    
    try:
        # Conectar con la base operacional de PostgreSQL
        pg_conn = psycopg2.connect(**POSTGRES_CONFIG)
        print("Conexión a PostgreSQL exitosa")
    except Exception as e:
        print(f"Error conectando a PostgreSQL: {e}")
        return None, None
    
    try:
        # Conectar con el Data Warehouse de Snowflake
        sf_conn = snowflake.connector.connect(**SNOWFLAKE_CONFIG)
        print("Conexión a Snowflake exitosa")
    except Exception as e:
        print(f"Error conectando a Snowflake: {e}")
        return pg_conn, None
    
    return pg_conn, sf_conn

# ==========================================
# EXTRACCIÓN DE DATOS HISTÓRICOS
# ==========================================

def extract_historical_data(pg_conn):
    """Extraer entregas históricas desde PostgreSQL"""

    query = """
        SELECT
            d.delivery_id,
            d.trip_id,
            d.tracking_number,
            d.customer_name,
            d.package_weight_kg,
            d.scheduled_datetime,
            d.delivered_datetime,
            d.delivery_status,
            d.recipient_signature,
            t.vehicle_id,
            t.driver_id,
            t.route_id,
            t.departure_datetime,
            t.arrival_datetime,
            t.fuel_consumed_liters,
            r.distance_km,
            r.toll_cost,
            r.destination_city
        FROM deliveries d
        JOIN trips t
            ON d.trip_id = t.trip_id
        JOIN routes r
            ON t.route_id = r.route_id
        WHERE d.delivered_datetime IS NOT NULL
    """

    try:
        df = pd.read_sql(query, pg_conn)
        print(f"Registros históricos extraídos: {len(df)}")
        return df

    except Exception as e:
        print(f"Error extrayendo datos históricos: {e}")
        return pd.DataFrame()

# ==========================================
# CARGA DE DIM_DATE
# ==========================================

def load_dim_date(df, sf_conn):
    """Crear y cargar las fechas necesarias en DIM_DATE"""

    # Obtener fecha mínima y máxima de las entregas
    start_date = pd.to_datetime(df['scheduled_datetime']).min().date()
    end_date = pd.to_datetime(df['delivered_datetime']).max().date()

    # Crear calendario completo entre ambas fechas
    dates = pd.date_range(start=start_date, end=end_date)

    # Preparar los registros
    date_data = []

    for date in dates:
        date_data.append((
            int(date.strftime('%Y%m%d')),
            date.date(),
            date.dayofweek + 1,
            date.day_name(),
            date.day,
            date.dayofyear,
            int(date.isocalendar().week),
            date.month,
            date.month_name(),
            date.quarter,
            date.year,
            date.dayofweek >= 5,
            False,
            None,
            date.quarter,
            date.year
        ))

    cursor = sf_conn.cursor()

    try:
        # Insertar todas las fechas en una sola operación
        cursor.executemany("""
            INSERT INTO dim_date (
                date_key,
                full_date,
                day_of_week,
                day_name,
                day_of_month,
                day_of_year,
                week_of_year,
                month_num,
                month_name,
                quarter,
                year,
                is_weekend,
                is_holiday,
                holiday_name,
                fiscal_quarter,
                fiscal_year
            )
            VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s, %s
            )
        """, date_data)

        sf_conn.commit()
        print(f"DIM_DATE cargada: {len(date_data)} fechas")

    except Exception as e:
        sf_conn.rollback()
        print(f"Error cargando DIM_DATE: {e}")

    finally:
        cursor.close()

# ==========================================
# CARGA DE DIM_TIME
# ==========================================

def load_dim_time(sf_conn):
    """Crear y cargar las horas del día en DIM_TIME"""

    time_data = []

    # Crear una fila por cada hora del día
    for hour in range(24):

        # Clasificar momento del día
        if hour < 6:
            time_of_day = 'Madrugada'
        elif hour < 12:
            time_of_day = 'Mañana'
        elif hour < 18:
            time_of_day = 'Tarde'
        else:
            time_of_day = 'Noche'

        # Clasificar turno
        if hour < 8:
            shift = 'Noche'
        elif hour < 16:
            shift = 'Mañana'
        else:
            shift = 'Tarde'

        time_data.append((
            hour * 100,
            hour,
            0,
            0,
            time_of_day,
            f"{hour:02d}:00",
            pd.Timestamp(year=2000, month=1, day=1, hour=hour).strftime('%I:%M %p'),
            'AM' if hour < 12 else 'PM',
            8 <= hour < 18,
            shift
        ))

    cursor = sf_conn.cursor()

    try:
        cursor.executemany("""
            INSERT INTO dim_time (
                time_key,
                hour,
                minute,
                second,
                time_of_day,
                hour_24,
                hour_12,
                am_pm,
                is_business_hour,
                shift
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            )
        """, time_data)

        sf_conn.commit()
        print(f"DIM_TIME cargada: {len(time_data)} registros")

    except Exception as e:
        sf_conn.rollback()
        print(f"Error cargando DIM_TIME: {e}")

    finally:
        cursor.close()

# ==========================================
# CARGA DE DIM_VEHICLE
# ==========================================

def load_dim_vehicle(pg_conn, sf_conn):
    """Extraer vehículos de PostgreSQL y cargar DIM_VEHICLE"""

    query = """
        SELECT
            v.vehicle_id,
            v.license_plate,
            v.vehicle_type,
            v.capacity_kg,
            v.fuel_type,
            v.acquisition_date,
            v.status,
            MAX(m.maintenance_date) AS last_maintenance_date
        FROM vehicles v
        LEFT JOIN maintenance m
            ON v.vehicle_id = m.vehicle_id
        GROUP BY
            v.vehicle_id,
            v.license_plate,
            v.vehicle_type,
            v.capacity_kg,
            v.fuel_type,
            v.acquisition_date,
            v.status
        ORDER BY v.vehicle_id
    """

    try:
        vehicles = pd.read_sql(query, pg_conn)

        vehicle_data = []

        for _, row in vehicles.iterrows():

            acquisition_date = pd.to_datetime(row['acquisition_date'])

            age_months = (
                (pd.Timestamp.today().year - acquisition_date.year) * 12
                + pd.Timestamp.today().month
                - acquisition_date.month
            )

            last_maintenance = (
                None
                if pd.isna(row['last_maintenance_date'])
                else pd.to_datetime(row['last_maintenance_date']).date()
            )

            vehicle_data.append((
                int(row['vehicle_id']),
                int(row['vehicle_id']),
                row['license_plate'],
                row['vehicle_type'],
                row['capacity_kg'],
                row['fuel_type'],
                acquisition_date.date(),
                age_months,
                row['status'],
                last_maintenance,
                acquisition_date.date(),
                None,
                True
            ))

        cursor = sf_conn.cursor()

        cursor.executemany("""
            INSERT INTO dim_vehicle (
                vehicle_key,
                vehicle_id,
                license_plate,
                vehicle_type,
                capacity_kg,
                fuel_type,
                acquisition_date,
                age_months,
                status,
                last_maintenance_date,
                valid_from,
                valid_to,
                is_current
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s
            )
        """, vehicle_data)

        sf_conn.commit()
        cursor.close()

        print(f"DIM_VEHICLE cargada: {len(vehicle_data)} vehículos")

    except Exception as e:
        sf_conn.rollback()
        print(f"Error cargando DIM_VEHICLE: {e}")

# ==========================================
# CARGA DE DIM_DRIVER
# ==========================================

def load_dim_driver(pg_conn, sf_conn):
    """Extraer conductores de PostgreSQL y cargar DIM_DRIVER"""

    query = """
        SELECT
            driver_id,
            employee_code,
            first_name,
            last_name,
            license_number,
            license_expiry,
            phone,
            hire_date,
            status
        FROM drivers
        ORDER BY driver_id
    """

    try:
        drivers = pd.read_sql(query, pg_conn)

        driver_data = []

        for _, row in drivers.iterrows():

            hire_date = pd.to_datetime(row['hire_date'])

            experience_months = (
                (pd.Timestamp.today().year - hire_date.year) * 12
                + pd.Timestamp.today().month
                - hire_date.month
            )

            full_name = f"{row['first_name']} {row['last_name']}"

            driver_data.append((
                int(row['driver_id']),
                int(row['driver_id']),
                row['employee_code'],
                full_name,
                row['license_number'],
                pd.to_datetime(row['license_expiry']).date(),
                row['phone'],
                hire_date.date(),
                experience_months,
                row['status'],
                'Medio',
                hire_date.date(),
                None,
                True
            ))

        cursor = sf_conn.cursor()

        cursor.executemany("""
            INSERT INTO dim_driver (
                driver_key,
                driver_id,
                employee_code,
                full_name,
                license_number,
                license_expiry,
                phone,
                hire_date,
                experience_months,
                status,
                performance_category,
                valid_from,
                valid_to,
                is_current
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s
            )
        """, driver_data)

        sf_conn.commit()
        cursor.close()

        print(f"DIM_DRIVER cargada: {len(driver_data)} conductores")

    except Exception as e:
        sf_conn.rollback()
        print(f"Error cargando DIM_DRIVER: {e}")

# ==========================================
# CARGA DE DIM_ROUTE
# ==========================================

def load_dim_route(pg_conn, sf_conn):
    """Extraer rutas de PostgreSQL y cargar DIM_ROUTE"""

    query = """
        SELECT
            route_id,
            route_code,
            origin_city,
            destination_city,
            distance_km,
            estimated_duration_hours,
            toll_cost
        FROM routes
        ORDER BY route_id
    """

    try:
        routes = pd.read_sql(query, pg_conn)

        route_data = []

        for _, row in routes.iterrows():

            # Clasificar la dificultad y el tipo según la distancia
            if row['distance_km'] < 100:
                difficulty_level = 'Baja'
                route_type = 'Corta'
            elif row['distance_km'] < 300:
                difficulty_level = 'Media'
                route_type = 'Media'
            else:
                difficulty_level = 'Alta'
                route_type = 'Larga'

            route_data.append((
                int(row['route_id']),
                int(row['route_id']),
                row['route_code'],
                row['origin_city'],
                row['destination_city'],
                row['distance_km'],
                row['estimated_duration_hours'],
                row['toll_cost'],
                difficulty_level,
                route_type
            ))

        cursor = sf_conn.cursor()

        cursor.executemany("""
            INSERT INTO dim_route (
                route_key,
                route_id,
                route_code,
                origin_city,
                destination_city,
                distance_km,
                estimated_duration_hours,
                toll_cost,
                difficulty_level,
                route_type
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s
            )
        """, route_data)

        sf_conn.commit()
        print(f"DIM_ROUTE cargada: {len(route_data)} rutas")

    except Exception as e:
        sf_conn.rollback()
        print(f"Error cargando DIM_ROUTE: {e}")

    finally:
        cursor.close()

# ==========================================
# CARGA DE DIM_CUSTOMER
# ==========================================

def load_dim_customer(df, sf_conn):
    """Crear clientes a partir de las entregas y cargar DIM_CUSTOMER"""

    # Agrupar las entregas por cliente
    customers = (
        df.groupby('customer_name')
        .agg(
            city=('destination_city', 'first'),
            first_delivery_date=('delivered_datetime', 'min'),
            total_deliveries=('delivery_id', 'count')
        )
        .reset_index()
    )

    customer_data = []

    for index, row in customers.iterrows():

        # Clasificar cliente según cantidad de entregas
        if row['total_deliveries'] >= 100:
            category = 'Frecuente'
        elif row['total_deliveries'] >= 20:
            category = 'Regular'
        else:
            category = 'Ocasional'

        customer_data.append((
            index + 1,
            row['customer_name'],
            'Individual',
            row['city'],
            pd.to_datetime(row['first_delivery_date']).date(),
            int(row['total_deliveries']),
            category
        ))

    cursor = sf_conn.cursor()

    try:
        # Insertar los clientes en lotes
        batch_size = 5000

        for i in range(0, len(customer_data), batch_size):
            batch = customer_data[i:i + batch_size]

            cursor.executemany("""
                INSERT INTO dim_customer (
                    customer_key,
                    customer_name,
                    customer_type,
                    city,
                    first_delivery_date,
                    total_deliveries,
                    customer_category
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s, %s
                )
            """, batch)

        sf_conn.commit()
        print(f"DIM_CUSTOMER cargada: {len(customer_data)} clientes")

    except Exception as e:
        sf_conn.rollback()
        print(f"Error cargando DIM_CUSTOMER: {e}")

    finally:
        cursor.close()

# ==========================================
# CARGA DE FACT_DELIVERIES
# ==========================================

def load_fact_deliveries(df, sf_conn):
    """Transformar entregas históricas y cargar FACT_DELIVERIES"""

    # Convertir fechas
    df['scheduled_datetime'] = pd.to_datetime(df['scheduled_datetime'])
    df['delivered_datetime'] = pd.to_datetime(df['delivered_datetime'])
    df['departure_datetime'] = pd.to_datetime(df['departure_datetime'])
    df['arrival_datetime'] = pd.to_datetime(df['arrival_datetime'])

    # Calcular tiempo transcurrido desde la salida del viaje hasta la entrega
    df['delivery_time_minutes'] = (
        (df['delivered_datetime'] - df['departure_datetime'])
        .dt.total_seconds() / 60
    )

    # Eliminar tiempos realmente inválidos antes de redondear
    df = df[df['delivery_time_minutes'] >= 0].copy()

    # Redondear después del control de calidad
    df['delivery_time_minutes'] = df['delivery_time_minutes'].round()

    # Calcular demora respecto al horario programado
    df['delay_minutes'] = (
        (df['delivered_datetime'] - df['scheduled_datetime'])
        .dt.total_seconds() / 60
    ).clip(lower=0).round()

    # Entrega a tiempo
    df['is_on_time'] = df['delay_minutes'] <= 30

    # Duración de cada viaje
    df['trip_duration_hours'] = (
        (df['arrival_datetime'] - df['departure_datetime'])
        .dt.total_seconds() / 3600
    )

    # Cantidad de entregas por viaje
    deliveries_per_trip = df.groupby('trip_id').size()
    df['deliveries_in_trip'] = df['trip_id'].map(deliveries_per_trip)

    # Entregas por hora
    df['deliveries_per_hour'] = (
        df['deliveries_in_trip'] / df['trip_duration_hours']
    ).round(2)

    # Eficiencia de combustible
    df['fuel_efficiency_km_per_liter'] = (
        df['distance_km'] / df['fuel_consumed_liters']
    ).round(2)

    # Costo estimado por entrega
    df['cost_per_delivery'] = (
        (df['fuel_consumed_liters'] * 5000 + df['toll_cost'])
        / df['deliveries_in_trip']
    ).round(2)

    # Ingreso estimado por entrega
    df['revenue_per_delivery'] = (
        20000 + df['package_weight_kg'] * 500
    ).round(2)

    # Obtener las claves de los clientes
    cursor = sf_conn.cursor()

    cursor.execute("""
        SELECT customer_key, customer_name
        FROM dim_customer
    """)

    customer_keys = {
        customer_name: customer_key
        for customer_key, customer_name in cursor.fetchall()
    }

    fact_data = []

    # Preparar registros para FACT_DELIVERIES
    for i, row in enumerate(df.itertuples(index=False), start=1):

        date_key = int(row.scheduled_datetime.strftime('%Y%m%d'))
        scheduled_time_key = row.scheduled_datetime.hour * 100
        delivered_time_key = row.delivered_datetime.hour * 100

        fact_data.append((
            date_key,
            scheduled_time_key,
            delivered_time_key,
            int(row.vehicle_id),
            int(row.driver_id),
            int(row.route_id),
            customer_keys[row.customer_name],
            int(row.delivery_id),
            int(row.trip_id),
            row.tracking_number,
            row.package_weight_kg,
            row.distance_km,
            row.fuel_consumed_liters,
            int(row.delivery_time_minutes),
            int(row.delay_minutes),
            row.deliveries_per_hour,
            row.fuel_efficiency_km_per_liter,
            row.cost_per_delivery,
            row.revenue_per_delivery,
            bool(row.is_on_time),
            False,
            bool(row.recipient_signature),
            row.delivery_status,
            1
        ))

        # Mostrar avance cada 50.000 registros
        if i % 50000 == 0:
            print(f"Preparando FACT_DELIVERIES: {i} registros...")

    try:
        # Insertar las entregas en lotes
        batch_size = 5000

        for i in range(0, len(fact_data), batch_size):
            batch = fact_data[i:i + batch_size]

            cursor.executemany("""
                INSERT INTO fact_deliveries (
                    date_key,
                    scheduled_time_key,
                    delivered_time_key,
                    vehicle_key,
                    driver_key,
                    route_key,
                    customer_key,
                    delivery_id,
                    trip_id,
                    tracking_number,
                    package_weight_kg,
                    distance_km,
                    fuel_consumed_liters,
                    delivery_time_minutes,
                    delay_minutes,
                    deliveries_per_hour,
                    fuel_efficiency_km_per_liter,
                    cost_per_delivery,
                    revenue_per_delivery,
                    is_on_time,
                    is_damaged,
                    has_signature,
                    delivery_status,
                    etl_batch_id
                )
                VALUES (
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s
                )
            """, batch)

        sf_conn.commit()
        print(f"FACT_DELIVERIES cargada: {len(fact_data)} entregas")

    except Exception as e:
        sf_conn.rollback()
        print(f"Error cargando FACT_DELIVERIES: {e}")

    finally:
        cursor.close()

# ==========================================
# EJECUCIÓN
# ==========================================

if __name__ == "__main__":

    pg_conn, sf_conn = connect_databases()

    if pg_conn and sf_conn:

        df = extract_historical_data(pg_conn)

        if not df.empty:

            print("\nIniciando carga inicial...")

            load_dim_date(df, sf_conn)
            load_dim_time(sf_conn)
            load_dim_vehicle(pg_conn, sf_conn)
            load_dim_driver(pg_conn, sf_conn)
            load_dim_route(pg_conn, sf_conn)
            load_dim_customer(df, sf_conn)
            load_fact_deliveries(df, sf_conn)

            print("\nCarga inicial finalizada")

        pg_conn.close()
        sf_conn.close()
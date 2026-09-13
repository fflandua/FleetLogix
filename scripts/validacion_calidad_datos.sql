-- =====================================================
-- FLEETLOGIX DATABASE VALIDATION
-- Verificación y control de calidad de los datos
-- =====================================================


-- 1. CANTIDAD DE REGISTROS
-- Verifica el volumen generado en cada tabla y permite
-- comparar los resultados con las cantidades esperadas.

SELECT COUNT(*) AS total_vehicles
FROM vehicles;

SELECT COUNT(*) AS total_drivers
FROM drivers;

SELECT COUNT(*) AS total_routes
FROM routes;

SELECT COUNT(*) AS total_trips
FROM trips;

SELECT COUNT(*) AS total_deliveries
FROM deliveries;

SELECT COUNT(*) AS total_maintenance
FROM maintenance;


-- 2. INTEGRIDAD REFERENCIAL
-- Busca registros cuyas claves foráneas no tengan
-- correspondencia en las tablas relacionadas.
-- El resultado esperado de cada consulta es 0.

-- Viajes asociados a vehículos inexistentes
SELECT COUNT(*) AS trips_sin_vehicle
FROM trips t
LEFT JOIN vehicles v
    ON t.vehicle_id = v.vehicle_id
WHERE v.vehicle_id IS NULL;

-- Viajes asociados a conductores inexistentes
SELECT COUNT(*) AS trips_sin_driver
FROM trips t
LEFT JOIN drivers d
    ON t.driver_id = d.driver_id
WHERE d.driver_id IS NULL;

-- Viajes asociados a rutas inexistentes
SELECT COUNT(*) AS trips_sin_route
FROM trips t
LEFT JOIN routes r
    ON t.route_id = r.route_id
WHERE r.route_id IS NULL;

-- Entregas asociadas a viajes inexistentes
SELECT COUNT(*) AS deliveries_sin_trip
FROM deliveries d
LEFT JOIN trips t
    ON d.trip_id = t.trip_id
WHERE t.trip_id IS NULL;

-- Mantenimientos asociados a vehículos inexistentes
SELECT COUNT(*) AS maintenance_sin_vehicle
FROM maintenance m
LEFT JOIN vehicles v
    ON m.vehicle_id = v.vehicle_id
WHERE v.vehicle_id IS NULL;


-- 3. CONSISTENCIA TEMPORAL
-- Busca viajes cuya llegada sea anterior o igual a la salida.
-- El resultado esperado es 0.

SELECT COUNT(*) AS trips_con_fechas_inconsistentes
FROM trips
WHERE arrival_datetime <= departure_datetime;
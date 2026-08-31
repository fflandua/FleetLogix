-- =====================================================
-- FLEETLOGIX DATABASE VALIDATION
-- Verificación y Control de Datos
-- =====================================================

-- 1. Verificar cantidad de registros en las tablas

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


-- 2. Validar integridad referencial completa

SELECT COUNT(*) AS trips_sin_vehicle
FROM trips t
LEFT JOIN vehicles v
    ON t.vehicle_id = v.vehicle_id
WHERE v.vehicle_id IS NULL;

SELECT COUNT(*) AS trips_sin_driver
FROM trips t
LEFT JOIN drivers d
    ON t.driver_id = d.driver_id
WHERE d.driver_id IS NULL;

SELECT COUNT(*) AS trips_sin_route
FROM trips t
LEFT JOIN routes r
    ON t.route_id = r.route_id
WHERE r.route_id IS NULL;

SELECT COUNT(*) AS deliveries_sin_trip
FROM deliveries d
LEFT JOIN trips t
    ON d.trip_id = t.trip_id
WHERE t.trip_id IS NULL;

SELECT COUNT(*) AS maintenance_sin_vehicle
FROM maintenance m
LEFT JOIN vehicles v
    ON m.vehicle_id = v.vehicle_id
WHERE v.vehicle_id IS NULL;


-- 3. Validar consistencia temporal de los viajes

SELECT COUNT(*) AS trips_con_fechas_inconsistentes
FROM trips
WHERE arrival_datetime <= departure_datetime;
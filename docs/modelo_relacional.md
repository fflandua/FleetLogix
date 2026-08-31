# Modelo Relacional - FleetLogix

## Relaciones del modelo

El modelo relacional de FleetLogix está compuesto por seis tablas: `vehicles`, `drivers`, `routes`, `trips`, `deliveries` y `maintenance`.

Las relaciones definidas mediante claves foráneas son:

- **vehicles → trips (1:N):** un vehículo puede estar asociado a muchos viajes. La relación se establece mediante `trips.vehicle_id`, que referencia a `vehicles.vehicle_id`.

- **drivers → trips (1:N):** un conductor puede estar asociado a muchos viajes. La relación se establece mediante `trips.driver_id`, que referencia a `drivers.driver_id`.

- **routes → trips (1:N):** una ruta puede estar asociada a muchos viajes. La relación se establece mediante `trips.route_id`, que referencia a `routes.route_id`.

- **trips → deliveries (1:N):** un viaje puede contener múltiples entregas. La relación se establece mediante `deliveries.trip_id`, que referencia a `trips.trip_id`.

- **vehicles → maintenance (1:N):** un vehículo puede registrar múltiples mantenimientos. La relación se establece mediante `maintenance.vehicle_id`, que referencia a `vehicles.vehicle_id`.

## Constraints

### Primary Keys

Cada tabla posee una clave primaria autoincremental definida mediante `SERIAL`:

- `vehicles`: `vehicle_id`
- `drivers`: `driver_id`
- `routes`: `route_id`
- `trips`: `trip_id`
- `deliveries`: `delivery_id`
- `maintenance`: `maintenance_id`

### Foreign Keys

- `trips.vehicle_id` → `vehicles.vehicle_id`
- `trips.driver_id` → `drivers.driver_id`
- `trips.route_id` → `routes.route_id`
- `deliveries.trip_id` → `trips.trip_id`
- `maintenance.vehicle_id` → `vehicles.vehicle_id`

### UNIQUE

El modelo evita duplicados en los siguientes campos:

- `vehicles.license_plate`
- `drivers.employee_code`
- `drivers.license_number`
- `routes.route_code`
- `deliveries.tracking_number`

### NOT NULL

Los siguientes campos son obligatorios:

- `vehicles`: `license_plate`, `vehicle_type`
- `drivers`: `employee_code`, `first_name`, `last_name`, `license_number`
- `routes`: `route_code`, `origin_city`, `destination_city`
- `trips`: `departure_datetime`
- `deliveries`: `tracking_number`, `customer_name`, `delivery_address`
- `maintenance`: `maintenance_date`, `maintenance_type`

### DEFAULT

El modelo establece los siguientes valores por defecto:

- `vehicles.status`: `'active'`
- `drivers.status`: `'active'`
- `routes.toll_cost`: `0`
- `trips.status`: `'in_progress'`
- `deliveries.delivery_status`: `'pending'`
- `deliveries.recipient_signature`: `FALSE`
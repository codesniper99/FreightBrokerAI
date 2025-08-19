INSERT INTO loads (
  load_id, origin, destination, pickup_datetime, delivery_datetime,
  equipment_type, loadboard_rate, notes, weight, commodity_type,
  num_of_pieces, miles, dimensions
) VALUES
('LD-1001','San Jose, CA','Sacramento, CA','2025-08-18T09:00:00Z','2025-08-18T15:00:00Z',
 'Van', 450.00, 'Fragile', 5, 'produce', 4, 118, '{"length":120,"width":80,"height":60,"unit":"cm"}'),
('LD-1002','Oakland, CA','San Francisco, CA','2025-08-19T08:00:00Z','2025-08-19T11:00:00Z',
 'Reefer', 900.00, 'Keep cold', 10, 'electronics', 6, 12, '{"length":150,"width":90,"height":80,"unit":"cm"}'),
('LD-1003','Fremont, CA','San Mateo, CA','2025-08-19T13:00:00Z','2025-08-19T16:00:00Z',
 'Flatbed', 700.00, NULL, 8, 'books', 10, 24, '{"length":200,"width":120,"height":90,"unit":"cm"}')
ON CONFLICT (load_id) DO NOTHING;
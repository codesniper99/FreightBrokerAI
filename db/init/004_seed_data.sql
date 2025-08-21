INSERT INTO events (source, name, status, duration_ms, route, payload)
VALUES
('webhook', 'load_search', 'ok', 120, '/webhook',
 '{"message": "Find loads from Chicago to Dallas", "weight_guess": "1000"}'),

('webhook', 'load_search', 'ok', 85, '/webhook',
 '{"message": "Show me loads near Atlanta", "limit": 3}'),

('system', 'health_check', 'ok', 5, '/health',
 '{"info": "service running"}'),

('webhook', 'load_match', 'ok', 240, '/webhook',
 '{"message": "Looking for 5000kg load", "weight_guess": "5000"}'),

('webhook', 'load_match', 'error', 300, '/webhook',
 '{"message": "Invalid payload received"}'),

('api', 'user_query', 'ok', 150, '/api/query',
 '{"query": "SELECT * FROM loads WHERE weight > 2000"}');
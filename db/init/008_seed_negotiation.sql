INSERT INTO negotiations
(session_id, load_id, miles, loadboard_rate, price,
 user_message, user_requested_price,
 cur_round, max_rounds,
 ai_negotiated_price, ai_negotiated_reason,
 history, ts, sentiment)
VALUES
(
  'sess-aaa', 'LD-1001', 118, 450, '450',
  'Asked for lower rate', '400',
  1, 3, '-1', '',
  '[{"round":1,"speaker":"user","message":"Can you do 400","price":400},{"round":1,"speaker":"system","message":"Best I can do is 450","price":450}]',
  NOW(), 'happy'
),
(
  'sess-bbb', 'LD-1002', 12, 900, '900',
  'User accepted the rate', 'ACCEPTED',
  1, 3, '900', 'Accepted initial offer',
  '[{"round":1,"speaker":"user","message":"Okay I will take it at 900","price":"ACCEPTED"}]',
  NOW(), 'neutral'
);

# Milestone 2 Implementation - Detailed Tasks

## Task 1: Update ml/classifier.py
- [ ] Add score_urgency(text) function that can be called by worker

## Task 2: Fix queue/async_broker.py
- [ ] Keep it thin - only push/pop/lock operations

## Task 3: Create worker.py (NEW FILE)
- [ ] Consume Redis queue
- [ ] Call transformer for urgency
- [ ] Trigger webhook if urgency > 0.8
- [ ] Add circuit breaker fallback (if >500ms use baseline)
- [ ] Add Redis lock for concurrency safety

## Task 4: Update app.py
- [ ] Push to queue instead of processing
- [ ] Return 202 Accepted

## Task 5: Create webhooks/notifications.py
- [ ] send_alert(ticket) function
- [ ] Support Slack and Discord

## Task 6: Test integration
- [ ] Verify all components work together

Mail Collector Celery Details
=============================

Data Collection
---------------

The mail borg events from all the bots are centralized via the Logstash
server and queued to the RabbitMQ server via the **logstash** exchange.
There is a **logstash** queue bound to that exchange and the Mail Collectgor
application is pulling in the events from that queue.

Celery Queues
-------------

Celery Worker Configuration
---------------------------

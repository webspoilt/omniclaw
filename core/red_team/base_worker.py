import redis
from rq import Queue, Connection, Worker
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseRedTeamWorker:
    """
    Base class for all OmniClaw workers.
    Subclasses must implement `process_task(data)`.
    """
    QUEUE_NAME = 'default'

    def __init__(self, redis_host='localhost', redis_port=6379, redis_db=0):
        self.redis_conn = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True
        )
        self.queue = Queue(self.QUEUE_NAME, connection=self.conn)

    @property
    def conn(self):
        return self.redis_conn

    def process_task(self, data):
        """Override this with actual task logic."""
        raise NotImplementedError

    def run(self):
        """Starts the worker listening for jobs."""
        with Connection(self.conn):
            worker = Worker([self.queue])
            worker.work()

    @staticmethod
    def enqueue_task(queue_name, task_data):
        """Utility to enqueue a task from the controller."""
        q = Queue(queue_name, connection=redis.Redis())
        job = q.enqueue('base_worker.dummy_task', task_data)  # Replace with actual worker function
        return job.id

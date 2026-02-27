import redis
from rq import Queue

def dispatch_recon_task(target):
    redis_conn = redis.Redis()
    q = Queue('recon', connection=redis_conn)
    job = q.enqueue('recon_worker.ReconWorker.process_task', {'target': target})
    print(f"Dispatched recon job {job.id} for {target}")

if __name__ == '__main__':
    dispatch_recon_task('example.com')

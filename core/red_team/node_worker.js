const Queue = require('bull');
const reconQueue = new Queue('recon', 'redis://127.0.0.1:6379');

// Add a task
reconQueue.add({ target: 'example.com' });

// Process jobs (Node.js worker)
reconQueue.process(async (job) => {
    console.log('Processing recon for', job.data.target);
    // Perform recon logic using Node libraries
    return { findings: [] };
});

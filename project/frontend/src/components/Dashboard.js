import React, { useState, useEffect } from 'react';
import { Container, TextField, Button, Paper, Typography, Box } from '@mui/material';
import AgentStatus from './AgentStatus';
import CostChart from './CostChart';
import { runAgentTask, fetchCosts } from '../api';

function Dashboard() {
    const [prompt, setPrompt] = useState('');
    const [output, setOutput] = useState('');
    const [costs, setCosts] = useState([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        loadCosts();
    }, []);

    const loadCosts = async () => {
        const res = await fetchCosts();
        setCosts(res.data);
    };

    const handleSubmit = async () => {
        setLoading(true);
        try {
            const res = await runAgentTask(prompt, null); // Note: conversationId is null for a fresh task
            setOutput(res.data.final_output);
            loadCosts(); // refresh costs after task
        } catch (err) {
            console.error(err);
            setOutput('Error: ' + err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Container maxWidth="lg" sx={{ mt: 4 }}>
            <Typography variant="h3" gutterBottom>Mission Control</Typography>
            <Box sx={{ display: 'flex', gap: 2, mb: 4 }}>
                <TextField
                    fullWidth
                    multiline
                    rows={3}
                    label="Enter your task"
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                />
                <Button variant="contained" onClick={handleSubmit} disabled={loading}>
                    {loading ? 'Running...' : 'Run Task'}
                </Button>
            </Box>
            <Box sx={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                <Paper sx={{ p: 2, flex: 1, minWidth: 300 }}>
                    <Typography variant="h5">Agent Output</Typography>
                    <pre style={{ whiteSpace: 'pre-wrap', wordWrap: 'break-word' }}>{output}</pre>
                </Paper>
                <Paper sx={{ p: 2, flex: 1, minWidth: 300 }}>
                    <Typography variant="h5">Agent Status</Typography>
                    <AgentStatus costs={costs} />
                </Paper>
            </Box>
            <Paper sx={{ p: 2, mt: 4 }}>
                <Typography variant="h5">Cost Tracker</Typography>
                <CostChart costs={costs} />
            </Paper>
        </Container>
    );
}

export default Dashboard;

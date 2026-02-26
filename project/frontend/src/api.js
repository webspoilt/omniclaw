import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000/api',
});

export const runAgentTask = (prompt, conversationId) =>
    api.post('/agents/task', { prompt, conversation_id: conversationId });

export const fetchCosts = () => api.get('/costs/');

export const executeTool = (toolName, parameters) =>
    api.post('/tools/execute', { tool_name: toolName, parameters });

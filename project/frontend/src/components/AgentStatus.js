import React from 'react';
import { List, ListItem, ListItemText, Chip, Box } from '@mui/material';

const agents = ['Architect', 'Coder', 'Reviewer'];

function AgentStatus({ costs }) {
    // Get last cost per agent (simple demo)
    const lastCosts = {};
    costs.forEach(c => {
        if (!lastCosts[c.agent] || new Date(c.timestamp) > new Date(lastCosts[c.agent].timestamp)) {
            lastCosts[c.agent] = c;
        }
    });

    return (
        <List>
            {agents.map(agent => {
                const cost = lastCosts[agent];
                return (
                    <ListItem key={agent}>
                        <ListItemText primary={agent} secondary={cost ? `Last cost: $${cost.cost_usd.toFixed(6)}` : 'No activity'} />
                        <Chip label="Active" color="success" size="small" />
                    </ListItem>
                );
            })}
        </List>
    );
}

export default AgentStatus;

import React from 'react';
import { Typography, Button } from '@mui/material';
import { useMutation } from 'react-query';
import axios from 'axios';

const Dashboard: React.FC = () => {
  const mutation = useMutation(() => axios.post('/api/webhooks/github', {}, { headers: { 'X-GitHub-Event': 'ping' } }));
  return (
    <div>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      <Typography variant="body1" gutterBottom>
        Welcome to the ai‑code‑review‑squad demo.  Use the Reviews tab to view reviews and run the demo review.
      </Typography>
      <Button variant="contained" color="primary" onClick={() => mutation.mutate()} disabled={mutation.isLoading}>
        Run Demo Review
      </Button>
    </div>
  );
};

export default Dashboard;
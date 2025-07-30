import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box } from '@mui/material';

import Layout from './components/Layout/Layout';
import Dashboard from './pages/Dashboard';
import ReviewList from './pages/ReviewList';
import ReviewDetail from './pages/ReviewDetail';
import RepositoryList from './pages/RepositoryList';
import AgentStatus from './pages/AgentStatus';

function App() {
  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/reviews" element={<ReviewList />} />
          <Route path="/reviews/:id" element={<ReviewDetail />} />
          <Route path="/repositories" element={<RepositoryList />} />
          <Route path="/agents" element={<AgentStatus />} />
        </Routes>
      </Layout>
    </Box>
  );
}

export default App;

import React from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Container, Button } from '@mui/material';
import Dashboard from './pages/Dashboard';
import Reviews from './pages/Reviews';
import ReviewDetailPage from './pages/ReviewDetailPage';
import Settings from './pages/Settings';

const App: React.FC = () => {
  return (
    <>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            ai-code-review-squad
          </Typography>
          <Button color="inherit" component={Link} to="/">Dashboard</Button>
          <Button color="inherit" component={Link} to="/reviews">Reviews</Button>
          <Button color="inherit" component={Link} to="/settings">Settings</Button>
        </Toolbar>
      </AppBar>
      <Container sx={{ mt: 4 }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/reviews" element={<Reviews />} />
          <Route path="/reviews/:id" element={<ReviewDetailPage />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Container>
    </>
  );
};

export default App;
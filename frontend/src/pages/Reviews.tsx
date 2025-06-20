import React from 'react';
import ReviewList from '../components/Reviews/ReviewList';
import React from 'react';
import { Typography, Button } from '@mui/material';

const Reviews: React.FC = () => {
  const [manifest, setManifest] = React.useState<any>(null);
  const [loadingManifest, setLoadingManifest] = React.useState(false);

  const fetchManifest = async () => {
    setLoadingManifest(true);
    try {
      const res = await fetch('/api/exports/analytics/latest-manifest');
      const data = await res.json();
      setManifest(data);
    } finally {
      setLoadingManifest(false);
    }
  };
  return (
    <div>
      <Typography variant="h4" gutterBottom>
        Reviews
      </Typography>
      <Button variant="outlined" onClick={fetchManifest} disabled={loadingManifest} sx={{ mb: 2 }}>
        Download Analytics Snapshot
      </Button>
      {manifest && (
        <pre style={{ background: '#f5f5f5', padding: '1em' }}>{JSON.stringify(manifest, null, 2)}</pre>
      )}
      <ReviewList />
    </div>
  );
};

export default Reviews;
import React from 'react';
import { Typography } from '@mui/material';

const Settings: React.FC = () => {
  return (
    <div>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>
      <Typography variant="body1">Feature flags and account settings will appear here.</Typography>
    </div>
  );
};

export default Settings;
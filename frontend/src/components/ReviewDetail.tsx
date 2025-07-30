import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  Box,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Alert,
  LinearProgress
} from '@mui/material';
import {
  Security,
  Speed,
  Code,
  Architecture,
  BugReport,
  CheckCircle,
  Warning,
  Error as ErrorIcon
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import { reviewsApi } from '../services/api';
import { formatDistanceToNow } from 'date-fns';

interface Finding {
  id: number;
  title: string;
  description: string;
  severity: string;
  confidence: number;
  file_path: string;
  line_number: number;
  code_snippet: string;
  suggestion: string;
  category: string;
  rule_id: string;
  agent_name: string;
}

interface Review {
  id: number;
  repository_id: number;
  status: string;
  branch: string;
  commit_sha?: string;
  created_at: string;
  completed_at?: string;
  summary?: any;
  findings_count: number;
}

const getSeverityColor = (severity: string) => {
  switch (severity.toLowerCase()) {
    case 'critical': return 'error';
    case 'high': return 'warning';
    case 'medium': return 'info';
    case 'low': return 'default';
    case 'info': return 'success';
    default: return 'default';
  }
};

const getSeverityIcon = (severity: string) => {
  switch (severity.toLowerCase()) {
    case 'critical': return <ErrorIcon />;
    case 'high': return <Warning />;
    case 'medium': return <BugReport />;
    case 'low': return <CheckCircle />;
    default: return <BugReport />;
  }
};

const getCategoryIcon = (category: string) => {
  switch (category.toLowerCase()) {
    case 'security': return <Security />;
    case 'performance': return <Speed />;
    case 'style': return <Code />;
    case 'architecture': return <Architecture />;
    case 'logic': return <BugReport />;
    default: return <BugReport />;
  }
};

export const ReviewDetail: React.FC = () => {
  const { reviewId } = useParams<{ reviewId: string }>();
  const navigate = useNavigate();
  const [review, setReview] = useState<Review | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSeverity, setSelectedSeverity] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  useEffect(() => {
    const fetchReviewData = async () => {
      if (!reviewId) return;

      try {
        setLoading(true);
        const [reviewData, findingsData] = await Promise.all([
          reviewsApi.getReview(parseInt(reviewId)),
          reviewsApi.getReviewFindings(parseInt(reviewId))
        ]);

        setReview(reviewData);
        setFindings(findingsData);
      } catch (err) {
        setError('Failed to load review data');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchReviewData();
  }, [reviewId]);

  const filteredFindings = findings.filter(finding => {
    if (selectedSeverity && finding.severity !== selectedSeverity) return false;
    if (selectedCategory && finding.category !== selectedCategory) return false;
    return true;
  });

  const severityCounts = findings.reduce((acc, finding) => {
    acc[finding.severity] = (acc[finding.severity] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const categoryCounts = findings.reduce((acc, finding) => {
    acc[finding.category] = (acc[finding.category] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  if (loading) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ mt: 4 }}>
          <Typography variant="h4" gutterBottom>
            Loading Review...
          </Typography>
          <LinearProgress />
        </Box>
      </Container>
    );
  }

  if (error || !review) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ mt: 4 }}>
          <Alert severity="error">
            {error || 'Review not found'}
          </Alert>
          <Button onClick={() => navigate('/reviews')} sx={{ mt: 2 }}>
            Back to Reviews
          </Button>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: 4, mb: 4 }}>
        {/* Header */}
        <Paper sx={{ p: 3, mb: 3 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Box>
              <Typography variant="h4" gutterBottom>
                Code Review #{review.id}
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Branch: {review.branch} | Created {formatDistanceToNow(new Date(review.created_at))} ago
              </Typography>
              {review.commit_sha && (
                <Typography variant="body2" color="text.secondary">
                  Commit: {review.commit_sha.substring(0, 8)}
                </Typography>
              )}
            </Box>
            <Box>
              <Chip
                label={review.status}
                color={review.status === 'COMPLETED' ? 'success' : 'primary'}
                sx={{ mr: 1 }}
              />
              <Button onClick={() => navigate('/reviews')}>
                Back to Reviews
              </Button>
            </Box>
          </Box>
        </Paper>

        {/* Summary Stats */}
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Findings by Severity
                </Typography>
                <List dense>
                  {Object.entries(severityCounts).map(([severity, count]) => (
                    <ListItem
                      key={severity}
                      button
                      onClick={() => setSelectedSeverity(selectedSeverity === severity ? null : severity)}
                      selected={selectedSeverity === severity}
                    >
                      <ListItemIcon>
                        {getSeverityIcon(severity)}
                      </ListItemIcon>
                      <ListItemText
                        primary={severity.charAt(0).toUpperCase() + severity.slice(1)}
                        secondary={`${count} findings`}
                      />
                      <Chip
                        label={count}
                        color={getSeverityColor(severity) as any}
                        size="small"
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Findings by Category
                </Typography>
                <List dense>
                  {Object.entries(categoryCounts).map(([category, count]) => (
                    <ListItem
                      key={category}
                      button
                      onClick={() => setSelectedCategory(selectedCategory === category ? null : category)}
                      selected={selectedCategory === category}
                    >
                      <ListItemIcon>
                        {getCategoryIcon(category)}
                      </ListItemIcon>
                      <ListItemText
                        primary={category.charAt(0).toUpperCase() + category.slice(1)}
                        secondary={`${count} findings`}
                      />
                      <Chip
                        label={count}
                        color="primary"
                        size="small"
                      />
                    </ListItem>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Filters */}
        <Paper sx={{ p: 2, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Filters
          </Typography>
          <Box display="flex" gap={2} flexWrap="wrap">
            {selectedSeverity && (
              <Chip
                label={`Severity: ${selectedSeverity}`}
                onDelete={() => setSelectedSeverity(null)}
                color="primary"
              />
            )}
            {selectedCategory && (
              <Chip
                label={`Category: ${selectedCategory}`}
                onDelete={() => setSelectedCategory(null)}
                color="primary"
              />
            )}
            <Typography variant="body2" color="text.secondary" sx={{ alignSelf: 'center' }}>
              Showing {filteredFindings.length} of {findings.length} findings
            </Typography>
          </Box>
        </Paper>

        {/* Findings List */}
        <Typography variant="h5" gutterBottom>
          Findings
        </Typography>
        
        {filteredFindings.length === 0 ? (
          <Alert severity="info">
            No findings match the current filters.
          </Alert>
        ) : (
          <Grid container spacing={2}>
            {filteredFindings.map((finding) => (
              <Grid item xs={12} key={finding.id}>
                <Card>
                  <CardContent>
                    <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                      <Box>
                        <Typography variant="h6" gutterBottom>
                          {finding.title}
                        </Typography>
                        <Box display="flex" gap={1} mb={1}>
                          <Chip
                            label={finding.severity}
                            color={getSeverityColor(finding.severity) as any}
                            size="small"
                            icon={getSeverityIcon(finding.severity)}
                          />
                          <Chip
                            label={finding.category}
                            size="small"
                            icon={getCategoryIcon(finding.category)}
                          />
                          <Chip
                            label={`${finding.confidence}% confidence`}
                            size="small"
                            variant="outlined"
                          />
                        </Box>
                      </Box>
                    </Box>

                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      {finding.file_path}:{finding.line_number}
                    </Typography>

                    <Typography variant="body1" paragraph>
                      {finding.description}
                    </Typography>

                    {finding.code_snippet && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Code:
                        </Typography>
                        <Paper
                          sx={{
                            p: 2,
                            backgroundColor: 'grey.100',
                            fontFamily: 'monospace',
                            fontSize: '0.875rem'
                          }}
                        >
                          {finding.code_snippet}
                        </Paper>
                      </Box>
                    )}

                    {finding.suggestion && (
                      <Box>
                        <Typography variant="subtitle2" gutterBottom>
                          Suggestion:
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {finding.suggestion}
                        </Typography>
                      </Box>
                    )}

                    <Divider sx={{ my: 2 }} />

                    <Box display="flex" justifyContent="space-between" alignItems="center">
                      <Typography variant="caption" color="text.secondary">
                        Rule: {finding.rule_id} | Agent: {finding.agent_name}
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </Box>
    </Container>
  );
};

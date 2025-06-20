import React from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from 'react-query';
import { getReview, getFindings, Review, Finding } from '../../lib/api';
import { CircularProgress, Typography, Table, TableHead, TableRow, TableCell, TableBody, Paper } from '@mui/material';

const ReviewDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { data: review, isLoading: loadingReview } = useQuery<Review>(['review', id], () => getReview(id!));
  const { data: findings, isLoading: loadingFindings } = useQuery<Finding[]>(['findings', id], () => getFindings(id!), { enabled: !!id });
  if (loadingReview || loadingFindings) return <CircularProgress />;
  if (!review) return <div>Review not found</div>;
  return (
    <div>
      <Typography variant="h5" gutterBottom>
        Review {review.id.slice(0, 8)} – PR {review.pr_number}
      </Typography>
      <Typography variant="subtitle1" gutterBottom>
        Status: {review.status}
      </Typography>
      <Typography variant="h6" gutterBottom>
        Findings
      </Typography>
      <Paper>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Severity</TableCell>
              <TableCell>Title</TableCell>
              <TableCell>File</TableCell>
              <TableCell>Line</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {findings?.map((f) => (
              <TableRow key={f.id}>
                <TableCell>{f.severity}</TableCell>
                <TableCell>{f.title}</TableCell>
                <TableCell>{f.file_path}</TableCell>
                <TableCell>{f.start_line}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
    </div>
  );
};

export default ReviewDetail;
import React from 'react';
import { useQuery } from 'react-query';
import { getReviews, Review } from '../../lib/api';
import { Link } from 'react-router-dom';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, CircularProgress } from '@mui/material';

const ReviewList: React.FC = () => {
  const { data, isLoading, error } = useQuery<Review[]>('reviews', getReviews);
  if (isLoading) return <CircularProgress />;
  if (error) return <div>Error loading reviews</div>;
  return (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>ID</TableCell>
            <TableCell>PR Number</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Created At</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {data?.map((review) => (
            <TableRow key={review.id} hover component={Link} to={`/reviews/${review.id}`} style={{ textDecoration: 'none' }}>
              <TableCell>{review.id.slice(0, 8)}</TableCell>
              <TableCell>{review.pr_number}</TableCell>
              <TableCell>{review.status}</TableCell>
              <TableCell>{new Date(review.created_at).toLocaleString()}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default ReviewList;
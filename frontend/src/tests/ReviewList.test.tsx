import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import ReviewList from '../components/Reviews/ReviewList';
import * as api from '../lib/api';

describe('ReviewList', () => {
  it('renders a list of reviews', async () => {
    vi.spyOn(api, 'getReviews').mockResolvedValue([
      { id: '1', repo_id: 'r', pr_number: '1', status: 'completed', created_at: new Date().toISOString(), updated_at: new Date().toISOString() },
    ]);
    render(<ReviewList />);
    expect(await screen.findByText('completed')).toBeDefined();
  });
});
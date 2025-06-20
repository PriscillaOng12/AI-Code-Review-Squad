import axios from 'axios';

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || 'http://localhost:8000'
});

export interface Review {
  id: string;
  repo_id: string;
  pr_number: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Finding {
  id: string;
  review_id: string;
  agent_run_id: string;
  file_path: string;
  start_line: number;
  end_line: number;
  severity: string;
  title: string;
  description: string;
  suggested_fix?: string;
  confidence?: number;
  rule_id?: string;
  created_at: string;
}

export async function getReviews(): Promise<Review[]> {
  const res = await apiClient.get<Review[]>('/api/reviews');
  return res.data;
}

export async function getReview(id: string): Promise<Review> {
  const res = await apiClient.get<Review>(`/api/reviews/${id}`);
  return res.data;
}

export async function getFindings(reviewId: string): Promise<Finding[]> {
  const res = await apiClient.get<Finding[]>(`/api/reviews/${reviewId}/findings`);
  return res.data;
}

export async function runDemoReview(): Promise<{ review_id: string }> {
  // Trigger webhook using local sample payload
  const payload = await fetch('/backend/app/demo/sample_payloads/pull_request_opened.json').then((r) => r.json());
  const res = await apiClient.post('/api/webhooks/github', payload, {
    headers: { 'X-GitHub-Event': 'pull_request' }
  });
  return res.data;
}
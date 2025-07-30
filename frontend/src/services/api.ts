import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export interface Repository {
  id: number;
  name: string;
  full_name: string;
  description?: string;
  private: boolean;
  default_branch: string;
  github_id: number;
  created_at: string;
  updated_at: string;
}

export interface Review {
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

export interface Finding {
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

export interface CreateReviewRequest {
  repository_id: number;
  branch?: string;
  commit_sha?: string;
  files?: string[];
  agents_config?: Record<string, any>;
  context?: Record<string, any>;
}

export interface User {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
}

// Auth API
export const authApi = {
  async login(email: string, password: string): Promise<{ access_token: string; user: User }> {
    const response = await apiClient.post('/auth/login', { email, password });
    return response.data;
  },

  async register(email: string, password: string, full_name: string): Promise<{ access_token: string; user: User }> {
    const response = await apiClient.post('/auth/register', { email, password, full_name });
    return response.data;
  },

  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get('/auth/me');
    return response.data;
  },

  async connectGitHub(code: string): Promise<{ success: boolean }> {
    const response = await apiClient.post('/auth/github/connect', { code });
    return response.data;
  },
};

// Repositories API
export const repositoriesApi = {
  async getRepositories(): Promise<Repository[]> {
    const response = await apiClient.get('/repositories');
    return response.data;
  },

  async getRepository(id: number): Promise<Repository> {
    const response = await apiClient.get(`/repositories/${id}`);
    return response.data;
  },

  async syncRepositories(): Promise<{ synced_count: number }> {
    const response = await apiClient.post('/repositories/sync');
    return response.data;
  },

  async deleteRepository(id: number): Promise<void> {
    await apiClient.delete(`/repositories/${id}`);
  },
};

// Reviews API
export const reviewsApi = {
  async getReviews(params?: {
    repository_id?: number;
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<Review[]> {
    const response = await apiClient.get('/reviews', { params });
    return response.data;
  },

  async getReview(id: number): Promise<Review> {
    const response = await apiClient.get(`/reviews/${id}`);
    return response.data;
  },

  async createReview(request: CreateReviewRequest): Promise<Review> {
    const response = await apiClient.post('/reviews', request);
    return response.data;
  },

  async getReviewFindings(
    reviewId: number,
    params?: {
      severity?: string;
      category?: string;
      agent?: string;
      limit?: number;
      offset?: number;
    }
  ): Promise<Finding[]> {
    const response = await apiClient.get(`/reviews/${reviewId}/findings`, { params });
    return response.data;
  },

  async deleteReview(id: number): Promise<void> {
    await apiClient.delete(`/reviews/${id}`);
  },
};

// WebSocket connection for real-time updates
export class WebSocketClient {
  private ws: WebSocket | null = null;
  private userId: number;
  private listeners: Map<string, Function[]> = new Map();

  constructor(userId: number) {
    this.userId = userId;
  }

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      const token = localStorage.getItem('access_token');
      const wsUrl = `${API_BASE_URL.replace('http', 'ws')}/ws/${this.userId}?token=${token}`;
      
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        resolve();
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        reject(error);
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        // Attempt to reconnect after 5 seconds
        setTimeout(() => this.connect(), 5000);
      };
    });
  }

  private handleMessage(message: any) {
    const { type } = message;
    const listeners = this.listeners.get(type) || [];
    
    listeners.forEach(listener => {
      try {
        listener(message);
      } catch (error) {
        console.error('Error in WebSocket listener:', error);
      }
    });
  }

  on(event: string, listener: Function) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event)!.push(listener);
  }

  off(event: string, listener: Function) {
    const listeners = this.listeners.get(event);
    if (listeners) {
      const index = listeners.indexOf(listener);
      if (index > -1) {
        listeners.splice(index, 1);
      }
    }
  }

  subscribeToReview(reviewId: number) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'subscribe_review',
        review_id: reviewId
      }));
    }
  }

  ping() {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ type: 'ping' }));
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export default apiClient;

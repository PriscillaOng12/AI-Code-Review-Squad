export interface User {
  id: number;
  tenant_id: number;
  email: string;
  role: string;
}

export function useCurrentUser(): User {
  // In mock mode we return a default user
  return { id: 1, tenant_id: 1, email: 'demo@example.com', role: 'Owner' };
}
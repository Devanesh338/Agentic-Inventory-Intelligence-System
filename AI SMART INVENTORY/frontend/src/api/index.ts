import { apiClient } from './client';

export const fetchHealth = async () => {
  const { data } = await apiClient.get('/health');
  return data;
};

export const fetchRegions = async (): Promise<string[]> => {
  const { data } = await apiClient.get('/regions');
  return data;
};

export const uploadDatasets = async (
  salesFile?: File,
  inventoryFile?: File,
  suppliersFile?: File
) => {
  const formData = new FormData();
  if (salesFile) formData.append('sales_file', salesFile);
  if (inventoryFile) formData.append('inventory_file', inventoryFile);
  if (suppliersFile) formData.append('suppliers_file', suppliersFile);

  const { data } = await apiClient.post('/ingestion/upload', formData);
  return data;
};

export const runOptimization = async (user_query: string, region: string) => {
  const { data } = await apiClient.post('/optimization/run', {
    user_query,
    region,
  });
  return data;
};

export const fetchAnalytics = async (endpoint: string, requestId: string) => {
  const { data } = await apiClient.get(`/analytics/${endpoint}/${requestId}`);
  return data;
};

export const submitApproval = async (requestId: string, decision: 'APPROVE' | 'REJECT', reason?: string) => {
  if (decision === 'APPROVE') {
    const { data } = await apiClient.post(`/approval/${requestId}/approve`, {
      approved_by: "human_user",
      comment: reason,
    });
    return data;
  } else {
    const { data } = await apiClient.post(`/approval/${requestId}/reject`, {
      rejected_by: "human_user",
      reason: reason || "User rejected",
    });
    return data;
  }
};

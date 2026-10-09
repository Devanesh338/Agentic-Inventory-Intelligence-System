import { create } from 'zustand';

interface AppState {
  // Region & Requirements
  selectedRegion: string | null;
  setSelectedRegion: (region: string | null) => void;
  
  userQuery: string;
  setUserQuery: (query: string) => void;

  // Ingestion
  ingestionStatus: 'idle' | 'loading' | 'success' | 'error';
  setIngestionStatus: (status: 'idle' | 'loading' | 'success' | 'error') => void;
  ingestionData: any;
  setIngestionData: (data: any) => void;
  
  // Optimization
  requestId: string | null;
  setRequestId: (id: string | null) => void;
  
  optimizationStatus: 'idle' | 'loading' | 'success' | 'error';
  setOptimizationStatus: (status: 'idle' | 'loading' | 'success' | 'error') => void;
  
  optimizationResult: any;
  setOptimizationResult: (result: any) => void;
  
  // Approval
  approvalStatus: 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED' | null;
  setApprovalStatus: (status: 'PENDING_APPROVAL' | 'APPROVED' | 'REJECTED' | null) => void;
  
  // Global
  clearSession: () => void;
}

export const useStore = create<AppState>((set) => ({
  selectedRegion: null,
  setSelectedRegion: (region) => set({ selectedRegion: region }),
  
  userQuery: '',
  setUserQuery: (query) => set({ userQuery: query }),
  
  ingestionStatus: 'idle',
  setIngestionStatus: (status) => set({ ingestionStatus: status }),
  ingestionData: null,
  setIngestionData: (data) => set({ ingestionData: data }),
  
  requestId: null,
  setRequestId: (id) => set({ requestId: id }),
  
  optimizationStatus: 'idle',
  setOptimizationStatus: (status) => set({ optimizationStatus: status }),
  
  optimizationResult: null,
  setOptimizationResult: (result) => set({ optimizationResult: result }),
  
  approvalStatus: null,
  setApprovalStatus: (status) => set({ approvalStatus: status }),
  
  clearSession: () => set({
    requestId: null,
    optimizationStatus: 'idle',
    optimizationResult: null,
    approvalStatus: null,
  })
}));

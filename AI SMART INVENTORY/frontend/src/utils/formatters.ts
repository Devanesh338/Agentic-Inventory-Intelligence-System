export const formatCurrency = (value: number | null | undefined): string => {
  if (value == null) return "N/A";
  return `₹${value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
};

export const formatPercentage = (value: number | null | undefined): string => {
  if (value == null) return "N/A";
  return `${(value * 100).toFixed(1)}%`;
};

export const formatReliability = (value: number | null | undefined): string => {
  if (value == null) return "N/A";
  return `${(value * 100).toFixed(0)}%`;
};

export const formatNumber = (value: number | null | undefined): string => {
  if (value == null) return "N/A";
  return value.toLocaleString('en-IN');
};

export const formatStatus = (status: string | null | undefined): string => {
  if (!status) return "N/A";
  return status.replace(/_/g, ' ');
};

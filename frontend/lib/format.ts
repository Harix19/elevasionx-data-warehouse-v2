/**
 * Format number as compact currency (Apollo-style)
 * e.g., 1500000 -> $1.5M, 500000 -> $500K
 */
export function formatCompactCurrency(value: number): string {
  if (value === null || value === undefined) return '';
  
  if (value >= 1_000_000_000) {
    return `$${(value / 1_000_000_000).toFixed(1).replace(/\.0$/, '')}B`;
  }
  if (value >= 1_000_000) {
    return `$${(value / 1_000_000).toFixed(1).replace(/\.0$/, '')}M`;
  }
  if (value >= 1_000) {
    return `$${(value / 1_000).toFixed(0)}K`;
  }
  return `$${value}`;
}

/**
 * Format number as compact (without currency symbol)
 * e.g., 1500000 -> 1.5M, 5000 -> 5K
 */
export function formatCompactNumber(value: number): string {
  if (value === null || value === undefined) return '';
  
  if (value >= 1_000_000_000) {
    return `${(value / 1_000_000_000).toFixed(1).replace(/\.0$/, '')}B`;
  }
  if (value >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(1).replace(/\.0$/, '')}M`;
  }
  if (value >= 1_000) {
    return `${(value / 1_000).toFixed(0)}K`;
  }
  return `${value}`;
}

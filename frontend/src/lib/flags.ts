export function useFeatureFlag(flag: string): boolean {
  const flags = (import.meta.env.VITE_FEATURE_FLAGS || '').split(',');
  return flags.includes(flag);
}
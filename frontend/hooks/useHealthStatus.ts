/**
 * Hook for checking backend health status
 */

'use client';

import { useEffect, useState } from 'react';
import { fetchHealth } from '@/lib/api';
import type { HealthStatus } from '@/lib/types';

export function useHealthStatus() {
  const [health, setHealth] = useState<HealthStatus>({
    isConnected: false,
    message: 'Checking...',
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function checkHealth() {
      try {
        const result = await fetchHealth();
        if (result?.status === 'ok') {
          setHealth({
            isConnected: true,
            message: 'Backend connected ✅',
          });
        } else {
          setHealth({
            isConnected: false,
            message: 'Backend not reachable ❌',
          });
        }
      } catch (error) {
        setHealth({
          isConnected: false,
          message: 'Backend not reachable ❌',
        });
      } finally {
        setIsLoading(false);
      }
    }

    checkHealth();
  }, []);

  return { ...health, isLoading };
}

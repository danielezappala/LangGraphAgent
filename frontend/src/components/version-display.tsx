"use client";

import { useEffect, useState } from 'react';
import { fetchVersion, getFrontendVersion } from '@/lib/api';
import { checkBackendStatus, getStatusTooltip, type BackendStatus } from '@/lib/backend-status';

// Mappa dei colori per ogni stato
const statusColors = {
  connected: '#10B981', // green-500
  inactive: '#9CA3AF',  // gray-400
  error: '#EF4444',    // red-500
  checking: '#F59E0B', // yellow-500
};
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Info, Circle } from 'lucide-react';

interface VersionInfo {
  version: string;
  build_date?: string;
  commit_hash?: string;
  status?: string;
  message?: string;
}

export function VersionDisplay() {
  const [backendVersion, setBackendVersion] = useState<VersionInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [backendStatus, setBackendStatus] = useState<BackendStatus>('checking');
  
  // Debug: log when status changes
  useEffect(() => {
    console.log('Backend status changed to:', backendStatus);
    console.log('Status color:', statusColors[backendStatus]);
  }, [backendStatus]);
  const frontendVersion = getFrontendVersion();

  // Check backend status periodically
  useEffect(() => {
    let isMounted = true;
    let timeoutId: NodeJS.Timeout;

    const checkStatus = async () => {
      if (!isMounted) return;
      
      try {
        // First check if the backend is reachable
        const status = await checkBackendStatus();
        if (!isMounted) return;
        
        setBackendStatus(status);
        
        // Only try to fetch version if backend is connected
        if (status === 'connected') {
          try {
            const version = await fetchVersion();
            if (isMounted) {
              setBackendVersion(version);
              setError(null);
            }
          } catch (err) {
            console.error('Failed to load version:', err);
            if (isMounted) {
              setError('Failed to load version information');
              setBackendStatus('error');
            }
          } finally {
            if (isMounted) {
              setIsLoading(false);
            }
          }
        } else {
          if (isMounted) {
            setIsLoading(false);
            setError('Backend non raggiungibile');
          }
        }
      } catch (err) {
        console.error('Error checking backend status:', err);
        if (isMounted) {
          setBackendStatus('error');
          setError('Errore di connessione');
          setIsLoading(false);
        }
      }
      
      // Schedule next status check (every 10 seconds)
      if (isMounted) {
        timeoutId = setTimeout(checkStatus, 10000);
      }
    };

    // Initial check
    checkStatus();

    // Cleanup function
    return () => {
      isMounted = false;
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5">
        <span>v{frontendVersion}</span>
        <span className="text-muted-foreground/60">| BE: Loading...</span>
        <div className="flex items-center">
          <Circle 
            className="h-2.5 w-2.5 rounded-full"
            style={{
              color: statusColors['checking'],
              fill: 'currentColor',
              animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
            }}
            aria-label="Verifica connessione in corso..."
          />
        </div>
      </div>
    );
  }

  // Non mostrare mai solo il messaggio di errore
  // Invece, mostralo accanto alle altre informazioni

  // Mostra sempre la versione del frontend e lo stato del backend
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors cursor-help">
            <span>v{frontendVersion}</span>
            <span className="text-muted-foreground/60">
              | BE: {backendVersion ? `v${backendVersion.version}` : 'N/A'}
            </span>
            <div className="flex items-center">
              <Circle 
                className="h-2.5 w-2.5 rounded-full"
                style={{
                  color: statusColors[backendStatus],
                  fill: 'currentColor',
                  animation: backendStatus === 'checking' ? 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite' : 'none',
                }}
                aria-label={getStatusTooltip(backendStatus)}
              />
            </div>
            {error && (
              <span className="text-red-500 text-xs ml-1">
                ({error})
              </span>
            )}
            <Info className="h-3 w-3 opacity-50" />
          </div>
        </TooltipTrigger>
        <TooltipContent className="max-w-xs p-3 text-xs">
          <div className="space-y-2">
            <div className="grid grid-cols-2 gap-x-2 gap-y-1">
              <span className="text-muted-foreground">Frontend:</span>
              <span className="font-mono">v{frontendVersion}</span>
              
              <span className="text-muted-foreground">Backend:</span>
              <span className="font-mono">
                {backendVersion ? `v${backendVersion.version}` : 'N/A'}
              </span>
              
              <span className="text-muted-foreground">Stato:</span>
              <div className="flex items-center gap-1">
                <Circle 
                  className="h-2.5 w-2.5 rounded-full"
                  style={{
                    color: statusColors[backendStatus],
                    fill: 'currentColor'
                  }}
                />
                <span>{getStatusTooltip(backendStatus)}</span>
              </div>
              
              {backendVersion?.build_date && (
                <>
                  <span className="text-muted-foreground">Build:</span>
                  <span className="font-mono text-xs">
                    {backendVersion.build_date}
                    {backendVersion.commit_hash && ` (${backendVersion.commit_hash.substring(0, 7)})`}
                  </span>
                </>
              )}
            </div>
          </div>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

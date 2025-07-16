'use client';

import { useState, useEffect } from 'react';

export default function TestPage() {
  const [response, setResponse] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const testBackendConnection = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
        console.log('Testing connection to:', `${apiUrl}/api/version/`);
        
        const res = await fetch(`${apiUrl}/api/version/`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (!res.ok) {
          throw new Error(`HTTP error! status: ${res.status}`);
        }

        const data = await res.json();
        setResponse(data);
      } catch (err) {
        console.error('Error fetching version:', err);
        setError(err instanceof Error ? err.message : 'Unknown error occurred');
      } finally {
        setIsLoading(false);
      }
    };

    testBackendConnection();
  }, []);

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Test Backend Connection</h1>
      
      <div className="mb-4 p-4 bg-gray-100 rounded">
        <h2 className="font-semibold mb-2">Environment Variables:</h2>
        <pre className="text-sm bg-white p-2 rounded overflow-auto">
          {JSON.stringify({
            NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
            NODE_ENV: process.env.NODE_ENV,
          }, null, 2)}
        </pre>
      </div>

      {isLoading ? (
        <div>Loading...</div>
      ) : error ? (
        <div className="text-red-600 p-4 bg-red-100 rounded">
          <h2 className="font-semibold">Error:</h2>
          <pre className="whitespace-pre-wrap">{error}</pre>
        </div>
      ) : (
        <div className="p-4 bg-green-50 rounded">
          <h2 className="font-semibold">Response from backend:</h2>
          <pre className="mt-2 p-2 bg-white rounded overflow-auto">
            {JSON.stringify(response, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

import React, { useState } from 'react';
import { Search, AlertCircle, Loader2 } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { searchEntities } from '../services/api';
import type { Entity } from '../types';

export function EntitySearch() {
  const [searchQuery, setSearchQuery] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');

  // Debounce search query
  React.useEffect(() => {
    const timeoutId = setTimeout(() => {
      setDebouncedQuery(searchQuery);
    }, 500);
    return () => clearTimeout(timeoutId);
  }, [searchQuery]);

  const { data: searchResults, isLoading, error } = useQuery({
    queryKey: ['entities', debouncedQuery],
    queryFn: () => searchEntities(debouncedQuery),
    enabled: debouncedQuery.length > 2,
    keepPreviousData: true,
  });

  const getRiskColor = (score: number) => {
    if (score < 30) return 'bg-green-100 text-green-800';
    if (score < 70) return 'bg-wf-gold bg-opacity-20 text-wf-black';
    return 'bg-wf-red bg-opacity-20 text-wf-red';
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow-sm">
        <div className="max-w-3xl mx-auto">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <label htmlFor="search" className="block text-sm font-medium text-wf-gray mb-2">
                Search entities
              </label>
              <div className="relative">
                <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
                  <Search className="h-5 w-5 text-wf-gray" />
                </div>
                <input
                  type="text"
                  name="search"
                  id="search"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="block w-full h-12 rounded-md border-wf-gray border-opacity-20 pl-10 pr-4 focus:border-wf-red focus:ring-wf-red text-base"
                  placeholder="Enter company name, individual, or location..."
                />
              </div>
              <p className="mt-2 text-sm text-wf-gray">
                Search for organizations, individuals, or locations to analyze risk factors
              </p>
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-wf-red bg-opacity-10 border-l-4 border-wf-red p-4 rounded-lg">
          <div className="flex">
            <div className="flex-shrink-0">
              <AlertCircle className="h-5 w-5 text-wf-red" />
            </div>
            <div className="ml-3">
              <p className="text-sm text-wf-red">
                An error occurred while searching. Please try again.
              </p>
            </div>
          </div>
        </div>
      )}

      {isLoading && (
        <div className="flex justify-center items-center py-8">
          <Loader2 className="h-8 w-8 text-wf-red animate-spin" />
        </div>
      )}

      {searchResults && searchResults.length > 0 && (
        <div className="bg-white shadow overflow-hidden sm:rounded-lg">
          <div className="px-4 py-5 sm:px-6">
            <h3 className="text-lg leading-6 font-medium text-wf-black">Search Results</h3>
          </div>
          <div className="border-t border-wf-gray border-opacity-20">
            {searchResults.map((entity) => (
              <div key={entity.id} className="px-4 py-5 sm:p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-lg font-medium text-wf-black">{entity.name}</h4>
                    <p className="mt-1 text-sm text-wf-gray">
                      {entity.type} • {entity.role}
                    </p>
                  </div>
                  <span
                    className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getRiskColor(
                      entity.riskScore
                    )}`}
                  >
                    Risk Score: {entity.riskScore}
                  </span>
                </div>

                {/* OFAC Sanctions Warning */}
                {entity.enrichmentData?.ofac?.sanctioned && (
                  <div className="mt-4 bg-wf-red bg-opacity-10 border-l-4 border-wf-red p-4">
                    <div className="flex">
                      <div className="flex-shrink-0">
                        <AlertCircle className="h-5 w-5 text-wf-red" />
                      </div>
                      <div className="ml-3">
                        <p className="text-sm text-wf-red">
                          This entity appears on OFAC sanctions lists
                        </p>
                        <ul className="mt-2 text-sm text-wf-red">
                          {entity.enrichmentData.ofac.listEntries.map((entry, index) => (
                            <li key={index}>
                              • {entry.list_name} ({entry.match_type} match)
                            </li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                )}

                {/* SEC Information */}
                {entity.enrichmentData?.sec && (
                  <div className="mt-4 bg-gray-50 rounded-md p-4">
                    <h5 className="text-sm font-medium text-wf-black mb-2">SEC Information</h5>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-wf-gray">Industry:</span>{' '}
                        <span className="text-wf-black">{entity.enrichmentData.sec.industry}</span>
                      </div>
                      <div>
                        <span className="text-wf-gray">State:</span>{' '}
                        <span className="text-wf-black">{entity.enrichmentData.sec.state}</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {searchResults && searchResults.length === 0 && debouncedQuery.length > 2 && (
        <div className="bg-gray-50 rounded-lg p-8 text-center">
          <p className="text-wf-gray">No entities found matching your search criteria.</p>
        </div>
      )}
    </div>
  );
}
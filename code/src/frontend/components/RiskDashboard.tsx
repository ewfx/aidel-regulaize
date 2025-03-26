import React from 'react';
import { BarChart3, TrendingUp, AlertTriangle, Shield, Loader2 } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { getTransactionStatistics, getRecentTransactions } from '../services/api';
import type { TransactionResponse } from '../types';
import clsx from 'clsx';

export function RiskDashboard() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['transactionStats'],
    queryFn: getTransactionStatistics,
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  const { data: recentTransactions, isLoading: transactionsLoading } = useQuery({
    queryKey: ['recentTransactions'],
    queryFn: () => getRecentTransactions(5),
    refetchInterval: 30000,
  });

  if (statsLoading || transactionsLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 text-wf-red animate-spin" />
      </div>
    );
  }

  const statCards = [
    {
      name: 'Total Transactions',
      value: stats?.totalCount.toLocaleString() || '0',
      change: '+4.75%',
      icon: BarChart3
    },
    {
      name: 'High Risk Entities',
      value: stats?.highRiskCount.toLocaleString() || '0',
      change: ((stats?.highRiskCount || 0) / (stats?.totalCount || 1) * 100).toFixed(1) + '%',
      icon: AlertTriangle
    },
    {
      name: 'Average Risk Score',
      value: (stats?.averageRiskScore || 0).toFixed(1),
      change: '+0.3%',
      icon: TrendingUp
    },
    {
      name: 'Compliance Rate',
      value: (stats?.complianceRate || 0).toFixed(1) + '%',
      change: '+1.2%',
      icon: Shield
    }
  ];

  const getRiskColor = (score: number) => {
    if (score < 0.3) return 'bg-green-100 text-green-800';
    if (score < 0.7) return 'bg-wf-gold bg-opacity-20 text-wf-black';
    return 'bg-wf-red bg-opacity-20 text-wf-red';
  };

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {statCards.map((item) => (
          <div
            key={item.name}
            className="relative bg-white pt-5 px-4 pb-12 sm:pt-6 sm:px-6 shadow rounded-lg overflow-hidden"
          >
            <dt>
              <div className="absolute bg-wf-red rounded-md p-3">
                <item.icon className="h-6 w-6 text-white" />
              </div>
              <p className="ml-16 text-sm font-medium text-wf-gray truncate">{item.name}</p>
            </dt>
            <dd className="ml-16 pb-6 flex items-baseline sm:pb-7">
              <p className="text-2xl font-semibold text-wf-black">{item.value}</p>
              <p
                className={clsx(
                  'ml-2 flex items-baseline text-sm font-semibold',
                  item.change.startsWith('+') ? 'text-green-600' : 'text-wf-red'
                )}
              >
                {item.change}
              </p>
            </dd>
          </div>
        ))}
      </div>

      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-wf-black">Risk Distribution</h3>
          <div className="mt-6">
            <div className="space-y-4">
              {[
                { 
                  label: 'Low Risk (0-30)',
                  value: (stats?.lowRiskCount || 0) / (stats?.totalCount || 1) * 100,
                  color: 'bg-green-500'
                },
                {
                  label: 'Medium Risk (31-70)',
                  value: (stats?.mediumRiskCount || 0) / (stats?.totalCount || 1) * 100,
                  color: 'bg-wf-gold'
                },
                {
                  label: 'High Risk (71-100)',
                  value: (stats?.highRiskCount || 0) / (stats?.totalCount || 1) * 100,
                  color: 'bg-wf-red'
                }
              ].map((item) => (
                <div key={item.label}>
                  <div className="flex items-center justify-between">
                    <div className="text-sm font-medium text-wf-gray">{item.label}</div>
                    <div className="text-sm font-medium text-wf-black">{item.value.toFixed(1)}%</div>
                  </div>
                  <div className="mt-1">
                    <div className="bg-wf-gray-light rounded-full overflow-hidden">
                      <div
                        className={`${item.color} h-2 rounded-full transition-all duration-500`}
                        style={{ width: `${item.value}%` }}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {recentTransactions && recentTransactions.length > 0 && (
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="px-4 py-5 sm:px-6">
            <h3 className="text-lg leading-6 font-medium text-wf-black">Recent Transactions</h3>
          </div>
          <div className="border-t border-wf-gray border-opacity-20">
            <ul className="divide-y divide-wf-gray divide-opacity-20">
              {recentTransactions.map((transaction: TransactionResponse) => (
                <li key={transaction.transactionId} className="px-4 py-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-wf-black">
                        Transaction {transaction.transactionId}
                      </p>
                      <p className="text-xs text-wf-gray mt-1">
                        {transaction.extractedEntities.join(', ')}
                      </p>
                    </div>
                    <div className="flex items-center space-x-4">
                      <span className={clsx(
                        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                        getRiskColor(transaction.riskScore)
                      )}>
                        Risk: {(transaction.riskScore * 100).toFixed(0)}
                      </span>
                      <span className="text-xs text-wf-gray">
                        Confidence: {(transaction.confidenceScore * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                  {transaction.reason && (
                    <p className="mt-2 text-sm text-wf-gray">{transaction.reason}</p>
                  )}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
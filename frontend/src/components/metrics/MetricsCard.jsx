import React from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { TrendingUp, TrendingDown } from 'lucide-react';

export const MetricsCard = ({ title, value, icon: Icon, trend, trendValue }) => {
  const isPositive = trend === 'up';

  return (
    <Card className="card-hover">
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-text-muted">{title}</p>
            <p className="text-3xl font-bold mt-2">{value}</p>
            
            {trend && trendValue !== undefined && (
              <div className={`flex items-center gap-1 mt-2 text-sm ${isPositive ? 'text-success' : 'text-error'}`}>
                {isPositive ? (
                  <TrendingUp className="w-4 h-4" />
                ) : (
                  <TrendingDown className="w-4 h-4" />
                )}
                <span>{trendValue}%</span>
              </div>
            )}
          </div>

          <div className="w-12 h-12 rounded-lg bg-gradient-to-r from-primary to-secondary flex items-center justify-center">
            <Icon className="w-6 h-6" />
          </div>
        </div>
      </CardContent>
    </Card>
  );
};


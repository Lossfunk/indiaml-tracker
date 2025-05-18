// src/components/shared/stat-card.tsx

import React from 'react';
import { StatCardProps } from '../../types/dashboard';


export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  icon,
  colorClass,
  subtitle,
  className = "",
}) => (
  <div
    className={`bg-card border border-border p-6 rounded-xl shadow-lg flex flex-col ${className}`}
  >
    {icon && (
      <>
        <div className="flex items-center gap-3">
          <div className={`${colorClass} text-2xl mb-3`}>{icon}</div>
          <div className="text-muted-foreground font-medium text-sm uppercase tracking-wider mb-2">
            {title}
          </div>
        </div>
      </>
    )}
    <p className={`text-4xl mt-5 md:text-5xl font-bold text-foreground mb-1`}>
      {value}
    </p>
    {subtitle && (
      <p className="text-muted-foreground text-xs mt-3">{subtitle}</p>
    )}
  </div>
);
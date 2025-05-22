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
    className={`bg-card border border-border p-6 rounded-xl shadow-lg hover:shadow-xl transition-shadow duration-300 flex flex-col ${className}`}
  >
    {icon && (
      <>
        <div className="flex items-center gap-3">
          <div className={`${colorClass} text-2xl mb-3 drop-shadow-sm`}>{icon}</div>
          <div className="text-muted-foreground font-medium text-sm uppercase tracking-wider mb-2">
            <span className="relative">
              {title}
              <span className="absolute bottom-0 left-0 w-0 bg-current h-0.5 group-hover:w-full transition-all duration-300 opacity-70"></span>
            </span>
          </div>
        </div>
      </>
    )}
    <p className={`text-4xl mt-5 md:text-5xl font-bold text-foreground mb-1 tracking-tight`}>
      {value}
    </p>
    {subtitle && (
      <p className="text-muted-foreground text-xs mt-3 leading-relaxed">{subtitle}</p>
    )}
  </div>
);
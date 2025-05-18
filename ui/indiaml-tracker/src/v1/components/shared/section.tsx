// src/components/shared/Section.tsx

import React from 'react';
import { SectionProps } from '../../types/dashboard';

/**
 * Layout section component used across the dashboard
 */
export const Section: React.FC<SectionProps> = ({
  title,
  subtitle,
  children,
  id,
  className = "",
}) => (
  <section
    id={id}
    className={`py-8 md:py-12 border-b border-border last:border-b-0 ${className}`}
  >
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <h2 className="text-2xl md:text-3xl font-bold text-foreground mb-2">
        {title}
      </h2>
      {subtitle && (
        <p className="text-base md:text-lg text-muted-foreground mb-6 md:mb-8">
          {subtitle}
        </p>
      )}
      {children}
    </div>
  </section>
);
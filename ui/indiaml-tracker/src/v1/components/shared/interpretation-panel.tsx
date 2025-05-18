// src/components/shared/interpretation-panel.tsx

import React from 'react';
import { FaLightbulb } from 'react-icons/fa';

interface InterpretationPanelProps {
  insights: string[];
  title?: string;
  icon?: React.ReactNode;
  iconColorClass?: string;
}


export const InterpretationPanel: React.FC<InterpretationPanelProps> = ({
  insights,
  title = "Key Insights",
  icon = <FaLightbulb />,
  iconColorClass = "text-amber-500 dark:text-amber-400",
}) => (
  <div className="mt-6 bg-muted/50 rounded-lg border border-border p-4">
    <div className="flex items-start mb-3">
      <span className={`mr-3 mt-1 flex-shrink-0 ${iconColorClass}`}>
        {icon}
      </span>
      <h4 className="text-base font-semibold text-foreground">{title}</h4>
    </div>
    <ul className="space-y-2 list-disc list-inside text-muted-foreground text-sm">
      {(insights || []).map((insight, idx) => (
        <li key={idx}>{insight}</li>
      ))}
    </ul>
  </div>
);
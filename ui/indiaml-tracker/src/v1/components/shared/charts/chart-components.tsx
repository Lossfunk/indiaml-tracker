// src/components/shared/charts/ChartComponents.tsx

import React from 'react';
import { TooltipProps } from 'recharts';

/**
 * Custom tooltip component for Recharts
 */
export const CustomTooltip: React.FC<TooltipProps<number, string>> = ({
  active,
  payload,
  label,
}) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    const formatValue = (val: any) =>
      typeof val === "number" ? val.toLocaleString() : String(val);
    const formatPercent = (val: any) =>
      typeof val === "number" ? `${(val * 100).toFixed(1)}%` : String(val);
    const formatDecimal = (val: any, places = 1) =>
      typeof val === "number" ? val.toFixed(places) : String(val);
    
    let title =
      label || data?.country_name || data?.institute || data?.name || "Details";
    
    if (data?.stage) title = data.stage;
    
    if (data?.type && (data.type === "Academic" || data.type === "Corporate"))
      title = data.type;

    return (
      <div className="bg-popover border border-border p-3 rounded-lg shadow-xl opacity-95 text-sm max-w-xs">
        <p className="text-muted-foreground font-medium mb-1 break-words">
          {title}
        </p>
        {payload.map((pld, index) => (
          <p
            key={index}
            style={{ color: pld.color || "hsl(var(--foreground))" }}
            className="break-words"
          >
            {`${pld.name}: ${formatValue(pld.value)}`}
            {pld.payload?.percent && ` (${formatPercent(pld.payload.percent)})`}
          </p>
        ))}
        {data?.rank && (
          <p className="text-muted-foreground text-xs mt-1">{`Rank: #${data.rank}`}</p>
        )}
        {data?.paper_count !== undefined &&
          !payload.some(
            (p) =>
              p.dataKey === "paper_count" || p.dataKey === "unique_paper_count"
          ) && (
            <p className="text-muted-foreground text-xs mt-1">{`Papers: ${formatValue(
              data.paper_count
            )}`}</p>
          )}
        {data?.unique_paper_count !== undefined &&
          !payload.some(
            (p) =>
              p.dataKey === "unique_paper_count" || p.dataKey === "paper_count"
          ) && (
            <p className="text-muted-foreground text-xs mt-1">{`Unique Papers: ${formatValue(
              data.unique_paper_count
            )}`}</p>
          )}
        {data?.author_count !== undefined &&
          data.author_count > 0 &&
          !payload.some(
            (p) => p.dataKey === "author_count" || p.name === "Authors"
          ) && (
            <p className="text-muted-foreground text-xs mt-1">{`Authors: ${formatValue(
              data.author_count
            )}`}</p>
          )}
        {data?.type &&
          (data.type === "academic" || data.type === "corporate") && (
            <p className="text-muted-foreground text-xs mt-1 capitalize">{`Type: ${data.type}`}</p>
          )}
        {data?.spotlight_oral_rate !== undefined && (
          <p className="text-muted-foreground text-xs mt-1">{`Spotlight/Oral Rate: ${formatPercent(
            data.spotlight_oral_rate
          )}`}</p>
        )}
        {data?.authors_per_paper !== undefined && (
          <p className="text-muted-foreground text-xs mt-1">{`Authors/Paper: ${formatDecimal(
            data.authors_per_paper,
            1
          )}`}</p>
        )}
        {(data?.spotlights !== undefined || data?.orals !== undefined) && (
          <p className="text-muted-foreground text-xs mt-1">
            Impact: {data.spotlights ?? 0} Spotlight(s), {data.orals ?? 0}{" "}
            Oral(s)
          </p>
        )}
        {data?.impact_score !== undefined &&
          !payload.some(
            (p) =>
              p.name === "Spotlights + Orals" ||
              p.name === "Impact (Spotlights+Orals)"
          ) && (
            <p className="text-muted-foreground text-xs mt-1">{`Impact (Spotlights+Orals): ${formatValue(
              data.impact_score
            )}`}</p>
          )}
      </div>
    );
  }
  return null;
};

/**
 * Active shape renderer for Recharts pie charts
 */
export const renderActiveShape = (props: any) => {
  const RADIAN = Math.PI / 180;
  const {
    cx = 0,
    cy = 0,
    midAngle = 0,
    innerRadius = 0,
    outerRadius = 0,
    startAngle = 0,
    endAngle = 0,
    fill = "hsl(var(--primary))",
    payload,
    percent = 0,
    value = 0,
    name = "",
  } = props;
  
  const sin = Math.sin(-RADIAN * midAngle);
  const cos = Math.cos(-RADIAN * midAngle);
  const sx = cx + (outerRadius + 10) * cos;
  const sy = cy + (outerRadius + 10) * sin;
  const mx = cx + (outerRadius + 30) * cos;
  const my = cy + (outerRadius + 30) * sin;
  const ex = mx + (cos >= 0 ? 1 : -1) * 22;
  const ey = my;
  const textAnchor = cos >= 0 ? "start" : "end";
  const textColor = "hsl(var(--foreground))";
  const mutedColor = "hsl(var(--muted-foreground))";

  return (
    <g>
      <text
        x={cx}
        y={cy}
        dy={8}
        textAnchor="middle"
        fill={textColor}
        fontSize="12"
        fontWeight="bold"
      >
        {payload?.name || name}
      </text>
      <Sector
        cx={cx}
        cy={cy}
        innerRadius={innerRadius}
        outerRadius={outerRadius}
        startAngle={startAngle}
        endAngle={endAngle}
        fill={fill}
      />
      <Sector
        cx={cx}
        cy={cy}
        startAngle={startAngle}
        endAngle={endAngle}
        innerRadius={outerRadius + 6}
        outerRadius={outerRadius + 10}
        fill={fill}
      />
      <path
        d={`M${sx},${sy}L${mx},${my}L${ex},${ey}`}
        stroke={fill}
        fill="none"
      />
      <circle cx={ex} cy={ey} r={2} fill={fill} stroke="none" />
      <text
        x={ex + (cos >= 0 ? 1 : -1) * 12}
        y={ey}
        textAnchor={textAnchor}
        fill={textColor}
        fontSize="11"
      >
        {`${value?.toLocaleString()}`}
      </text>
      <text
        x={ex + (cos >= 0 ? 1 : -1) * 12}
        y={ey}
        dy={18}
        textAnchor={textAnchor}
        fill={mutedColor}
        fontSize="10"
      >
        {`(${(percent * 100).toFixed(1)}%)`}
      </text>
    </g>
  );
};

/**
 * Custom label render function for pie charts
 */
export const renderCustomizedLabel = ({
  cx,
  cy,
  midAngle,
  innerRadius,
  outerRadius,
  percent,
  index,
  name,
  value,
}: any) => {
  const RADIAN = Math.PI / 180;
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);
  const percentValue = (percent * 100).toFixed(0);
  
  if (percent < 0.05) return null;
  
  return (
    <text
      x={x}
      y={y}
      fill="white"
      textAnchor={x > cx ? "start" : "end"}
      dominantBaseline="central"
      fontSize="10"
      fontWeight="bold"
    >
      {`${name.substring(0, 10)}${
        name.length > 10 ? "..." : ""
      } ${percentValue}%`}
    </text>
  );
};

// Import these components to prevent "Sector" not defined error
import { Sector } from 'recharts';

/**
 * TabButton component for tabbed interfaces
 */
export interface TabButtonProps {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
  icon?: React.ReactNode;
}

export const TabButton: React.FC<TabButtonProps> = ({
  active,
  onClick,
  children,
  icon,
}) => (
  <button
    onClick={onClick}
    className={`flex items-center justify-center px-4 py-2 text-sm font-medium rounded-t-lg transition-colors ${
      active
        ? "bg-card text-foreground border-t border-l border-r border-border"
        : "bg-muted text-muted-foreground hover:bg-muted/80"
    }`}
  >
    {icon && <span className="mr-2">{icon}</span>}
    {children}
  </button>
);

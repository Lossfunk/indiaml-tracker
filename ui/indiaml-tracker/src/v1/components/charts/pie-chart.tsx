import React from 'react';
import { chartColors } from '../../utils/chart-colors';
import {
  ResponsiveContainer,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  Tooltip,
  Legend
} from 'recharts';

interface PieChartDataItem {
  name: string;
  value: number;
  fill?: string;
  color?: string;
  percent?: number;
}

interface PieChartProps {
  data: PieChartDataItem[];
  title?: string;
  width?: string | number;
  height?: number;
  showLabels?: boolean;
  showTooltip?: boolean;
  showLegend?: boolean;
  className?: string;
  innerRadius?: number;
  outerRadius?: number;
  labelLine?: boolean;
  labelFormatter?: (value: any) => string;
}

export const PieChart: React.FC<PieChartProps> = ({
  data,
  title,
  width = '100%',
  height = 300,
  showLabels = false,
  showTooltip = true,
  showLegend = true,
  className = '',
  innerRadius = 0,
  outerRadius = 80,
  labelLine = true,
  labelFormatter
}) => {
  // Don't render if no data
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-full min-h-[200px] bg-muted/20 rounded-lg border border-border animate-pulse shadow-inner">
        <span className="text-muted-foreground">Visualization dataset unavailable</span>
      </div>
    );
  }

  // Calculate percentages for labels
  const total = data.reduce((sum, item) => sum + item.value, 0);
  
  // Custom label formatter
  const renderCustomizedLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent, index, name }: any) => {
    if (!showLabels) return null;
    
    const RADIAN = Math.PI / 180;
    const radius = innerRadius + (outerRadius - innerRadius) * 0.6;
    const x = cx + radius * Math.cos(-midAngle * RADIAN);
    const y = cy + radius * Math.sin(-midAngle * RADIAN);
    
    return (
      <text 
        x={x} 
        y={y} 
        fill="hsl(var(--foreground))"
        fontWeight={500}
        textAnchor={x > cx ? 'start' : 'end'} 
        dominantBaseline="central"
        style={{ fontSize: '0.75rem', fontWeight: 600 }}
      >
        {labelFormatter 
          ? labelFormatter(data[index]) 
          : `${(percent * 100).toFixed(0)}%`}
      </text>
    );
  };

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const item = payload[0];
      const percentage = ((item.value / total) * 100).toFixed(1);
      
      return (
        <div className="bg-card p-4 border border-border rounded-lg shadow-lg backdrop-blur-md bg-opacity-95 dark:bg-opacity-90">
          <p className="font-medium text-sm mb-2.5 border-b border-border pb-2">{item.name}</p>
          <div className="flex items-center gap-2">
            <div
              className="w-4 h-4 rounded-full"
              style={{
                backgroundColor: item.payload.fill || item.payload.color,
                boxShadow: `0 0 10px 0 ${item.payload.fill || item.payload.color}80`
              }}
            ></div>
            <div className="text-xs">
              <span className="font-bold">{item.value}</span>
              <span className="text-muted-foreground ml-2">({percentage}%)</span>
            </div>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className={`w-full ${className}`}>
      {title && (
        <h4 className="text-xs mt-3 font-semibold text-center mb-3.5 text-foreground tracking-tight">{title}</h4>
      )}
      <ResponsiveContainer width={width} height={height}>
        <RechartsPieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            labelLine={labelLine && showLabels}
            label={renderCustomizedLabel}
            innerRadius={innerRadius}
            outerRadius={outerRadius}
            paddingAngle={4}
            dataKey="value"
            animationDuration={1200}
            animationEasing="ease-in-out"
          >
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.fill || entry.color || chartColors.getPieChartColors(data.length)[index]}
                stroke="hsl(var(--background))"
                strokeWidth={1}
                style={{ filter: 'drop-shadow(0 6px 12px rgba(0, 0, 0, 0.32))' }}
              />
            ))}
          </Pie>
          {showTooltip && <Tooltip content={<CustomTooltip />} />}
          {showLegend && (
            <Legend
              layout="horizontal"
              verticalAlign="bottom"
              align="center"
              wrapperStyle={{
                fontSize: '0.75rem',
                paddingTop: '24px',
                fontWeight: 500
              }}
              iconType="circle"
              iconSize={10}
            />
          )}
        </RechartsPieChart>
      </ResponsiveContainer>
    </div>
  );
};
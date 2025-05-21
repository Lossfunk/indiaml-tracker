import React from 'react';
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
      <div className="flex items-center justify-center h-full min-h-[200px] bg-muted/20 rounded-lg border border-border">
        <span className="text-muted-foreground">No data available</span>
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
        textAnchor={x > cx ? 'start' : 'end'} 
        dominantBaseline="central"
        style={{ fontSize: '0.75rem', fontWeight: 500 }}
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
        <div className="bg-card p-2 border border-border rounded-md shadow-sm text-xs">
          <p className="font-medium mb-1">{item.name}</p>
          <p className="text-muted-foreground">
            {item.value} ({percentage}%)
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className={`w-full ${className}`}>
      {title && (
        <h4 className="text-sm font-medium text-center mb-3 text-foreground">{title}</h4>
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
            paddingAngle={2}
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.fill || `hsl(${index * 45}, 70%, 60%)`} />
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
                paddingTop: '10px'
              }}
            />
          )}
        </RechartsPieChart>
      </ResponsiveContainer>
    </div>
  );
};
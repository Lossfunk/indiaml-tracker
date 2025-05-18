// src/components/shared/DataTable.tsx

import React, { useCallback } from 'react';
import { FaDownload } from 'react-icons/fa';
import { exportToCSV } from '../../utils/export-utils';

interface DataTableProps {
  data: Record<string, string | number | boolean | undefined | null>[];
  title: string;
  filename: string;
}

/**
 * Generic data table with export capability
 */
export const DataTable: React.FC<DataTableProps> = ({ data, title, filename }) => {
  if (!data || data.length === 0) {
    return (
      <div className="text-muted-foreground p-4">
        No data available for the table.
      </div>
    );
  }
  
  const headers = data.length > 0 ? Object.keys(data[0]) : [];
  const handleExport = useCallback(
    () => exportToCSV(data, filename),
    [data, filename]
  );

  return (
    <div className="overflow-x-auto mt-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 gap-3">
        <h4 className="text-foreground font-medium text-lg">{title}</h4>
        <button
          onClick={handleExport}
          className="flex items-center bg-primary hover:bg-primary/90 text-primary-foreground text-xs px-3 py-1.5 rounded transition-colors shadow-sm"
          aria-label={`Export ${title} data to CSV`}
        >
          <FaDownload className="mr-1.5" size={10} /> Export CSV
        </button>
      </div>
      <div className="border border-border rounded-lg overflow-hidden shadow-sm">
        <table className="min-w-full divide-y divide-border">
          <thead className="bg-muted">
            <tr>
              {headers.map((header) => (
                <th
                  key={header}
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider whitespace-nowrap"
                >
                  {header
                    .replace(/_/g, " ")
                    .replace(/\b\w/g, (l) => l.toUpperCase())}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-card divide-y divide-border">
            {data.map((row, rowIndex) => (
              <tr
                key={rowIndex}
                className={`${
                  row.highlight
                    ? "bg-amber-100 dark:bg-amber-900/30 font-medium"
                    : ""
                } hover:bg-muted/50 transition-colors`}
              >
                {headers.map((header, colIndex) => (
                  <td
                    key={`${rowIndex}-${colIndex}`}
                    className="px-6 py-4 whitespace-nowrap text-sm text-card-foreground"
                  >
                    {Array.isArray(row[header])
                      ? (row[header] as (string | number)[])
                          .slice(0, 3)
                          .join(", ") +
                        ((row[header] as any[]).length > 3 ? "..." : "")
                      : typeof row[header] === "boolean"
                      ? row[header]
                        ? "Yes"
                        : "No"
                      : row[header]?.toLocaleString() ?? ""}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

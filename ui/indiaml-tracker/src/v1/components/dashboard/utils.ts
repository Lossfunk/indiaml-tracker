// Utility functions for the dashboard

/**
 * Export data to CSV file
 */
export const exportToCSV = (data: Record<string, any>[], filename: string): void => {
    if (!data || data.length === 0) {
        console.warn("Export Aborted: No data provided.");
        return;
    }
    try {
        const headers = Object.keys(data[0]);
        const csvContent = [
            headers.join(','),
            ...data.map(row => headers.map(header => {
                const value = row[header] !== undefined && row[header] !== null ? row[header] : '';
                let stringValue = String(value);
                stringValue = stringValue.replace(/"/g, '""');
                if (stringValue.includes(',')) {
                    stringValue = `"${stringValue}"`;
                }
                return stringValue;
            }).join(','))
        ].join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.setAttribute('href', url);
        link.setAttribute('download', `${filename}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    } catch (error) {
        console.error("Error exporting to CSV:", error);
    }
};

// src/v1/utils/export-utils.ts

/**
 * Exports data to CSV and triggers a download
 * @param data Array of objects to export
 * @param filename Name for the downloaded file (without extension)
 */
export const exportToCSV = (data: Record<string, any>[], filename: string): void => {
    if (!data || data.length === 0) {
      console.warn("Export Aborted: No data provided.");
      return;
    }
    
    try {
      const headers = Object.keys(data[0]);
      const csvContent = [
        headers.join(","),
        ...data.map((row) =>
          headers
            .map((header) => {
              const value =
                row[header] !== undefined && row[header] !== null
                  ? row[header]
                  : "";
              let stringValue = String(value);
              if (Array.isArray(value)) {
                stringValue = value.join("; ");
              }
              stringValue = stringValue.replace(/"/g, '""');
              if (stringValue.includes(",")) {
                stringValue = `"${stringValue}"`;
              }
              return stringValue;
            })
            .join(",")
        ),
      ].join("\n");
      
      const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.setAttribute("href", url);
      link.setAttribute("download", `${filename}.csv`);
      link.style.visibility = "hidden";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error("Error exporting to CSV:", error);
    }
  };
  
  /**
   * Export institution data in a standardized format
   */
  export const exportInstitutionData = (
    institutions: Array<any>,
    focusCountryCode: string,
    conferenceName: string,
    year: number
  ): void => {
    exportToCSV(
      institutions.map((inst) => ({
        Institution: inst.institute,
        Type: inst.type || "Unknown",
        Papers: inst.total_paper_count,
        Authors_Count: inst.author_count,
        Authors_List: inst.authors?.join("; ") || "",
        Authors_Per_Paper: inst.authors_per_paper?.toFixed(1),
        Spotlights: inst.spotlights,
        Orals: inst.orals,
        Impact_Score: inst.impact_score,
      })),
      `detailed_${focusCountryCode.toLowerCase()}_institutions_${conferenceName
        .toLowerCase()
        .replace(/\s+/g, "_")}_${year}`
    );
  };
  
// src/services/dashboard-api.ts

import { DashboardDataInterface, TrackerIndexEntry } from '../types/dashboard';

/**
 * Fetches the list of available conferences from the index.json file
 * @returns Array of conference options
 */
export const fetchConferenceOptions = async (): Promise<TrackerIndexEntry[]> => {
  const response = await fetch("/tracker/index.json");
  if (!response.ok) {
    throw new Error(
      `Failed to fetch conference list: ${response.status} ${response.statusText}`
    );
  }
  
  const data: TrackerIndexEntry[] = await response.json();
  
  // Sort by year (desc) then by label (asc)
  return data.sort((a, b) => {
    const yearComparison = parseInt(b.year, 10) - parseInt(a.year, 10);
    if (yearComparison !== 0) return yearComparison;
    return a.label.localeCompare(b.label);
  });
};

/**
 * Fetches dashboard data for a specific conference and year
 * @param conference Conference code
 * @param year Conference year
 * @returns Dashboard data
 */
export const fetchDashboardData = async (
  conference: string,
  year: string
): Promise<DashboardDataInterface> => {
  if (!conference || !year) {
    throw new Error("Conference and year must be provided");
  }
  
  // First, get the index to find the analytics file path
  const indexResponse = await fetch("/tracker/index.json");
  if (!indexResponse.ok) {
    throw new Error(
      `Failed to fetch index: ${indexResponse.status} ${indexResponse.statusText}`
    );
  }
  
  const indexData: TrackerIndexEntry[] = await indexResponse.json();
  const conferenceEntry = indexData.find(
    (item) =>
      item.venue.toLowerCase() === conference.toLowerCase() &&
      String(item.year) === String(year)
  );
  
  if (!conferenceEntry || !conferenceEntry.analytics) {
    throw new Error(
      `No analytics data found for ${conference.toUpperCase()} ${year}`
    );
  }
  
  // Now fetch the actual dashboard data
  const analyticsUrl = `/tracker/${conferenceEntry.analytics}`;
  const analyticsResponse = await fetch(analyticsUrl);
  
  if (!analyticsResponse.ok) {
    throw new Error(
      `Failed to fetch analytics data: ${analyticsResponse.status} ${analyticsResponse.statusText}`
    );
  }
  
  return await analyticsResponse.json() as DashboardDataInterface;
};

/**
 * Helper to get URL parameters
 */
export const getUrlParameters = (): { conference?: string; year?: string } => {
  const params = new URLSearchParams(window.location.search);
  return {
    conference: params.get('conference') || undefined,
    year: params.get('year') || undefined
  };
};

/**
 * Updates URL with current conference and year
 */
export const updateUrlParameters = (conference: string, year: string): void => {
  const newUrl = `${window.location.pathname}?conference=${conference}&year=${year}${window.location.hash}`;
  window.history.pushState({ path: newUrl }, '', newUrl);
};

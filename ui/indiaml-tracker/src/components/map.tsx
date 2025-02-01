import React from 'react';
import Plot from 'react-plotly.js';

// Example helper: transform the author count similar to your Python function
const threshold = 6000;
const transformCount = (x, maxCount) => {
  if (x <= threshold) {
    return Math.log10(x + 1); // log10 for interpretability
  } else {
    return Math.log10(threshold + 1) + (x - threshold) / (maxCount - threshold);
  }
};

const ChoroplethMap = ({ data, title = 'Choropleth Map' }) => {
  // `data` should be an array of objects with at least:
  // { country: "Country Name", iso_code: "ISO", author_count: number }
  if (!data || data.length === 0) return <div>No data available.</div>;

  // Compute maxCount from the data
  const maxCount = Math.max(...data.map(d => d.author_count));

  // Preprocess data: compute transformed and normalized values.
  // Define the minimum and maximum transformed values.
  const tMin = Math.log10(1); // log10(0+1) = 0
  const tMax = Math.log10(threshold + 1) + 1; // as in your python code

  const processedData = data.map(d => {
    const transformed = transformCount(d.author_count, maxCount);
    const normalized = (transformed - tMin) / (tMax - tMin);
    return { ...d, transformed, normalized };
  });

  // Create arrays for the Plotly data.
  const isoCodes = processedData.map(d => d.iso_code);
  const normalizedValues = processedData.map(d => d.normalized);
  const countries = processedData.map(d => d.country);
  const authorCounts = processedData.map(d => d.author_count);

  // Define the tick values as in your python code.
  const tickValuesRaw = [1, 10, 100, 1000, threshold, maxCount];
  const tickTransformed = tickValuesRaw.map(v => transformCount(v, maxCount));
  const tickNormalized = tickTransformed.map(t => (t - tMin) / (tMax - tMin));

  return (
    <Plot
      data={[
        {
          type: 'choropleth',
          locations: isoCodes,
          z: normalizedValues,
          text: countries,
          hoverinfo: 'text+z',
          // Build a custom hover text showing the author count
          hovertext: processedData.map(d => `${d.country}<br>Authors: ${d.author_count}`),
          colorscale: 'Mint',
          colorbar: {
            title: 'Number of Authors',
            tickvals: tickNormalized,
            ticktext: tickValuesRaw.map(String),
          },
        },
      ]}
      layout={{
        title: title,
        geo: {
          showframe: false,
          showcoastlines: false,
          projection: { type: 'natural earth' },
        },
        margin: { r: 0, t: 40, l: 0, b: 0 },
      }}
      style={{ width: '100%', height: '100%' }}
      useResizeHandler={true}
    />
  );
};

export default ChoroplethMap;

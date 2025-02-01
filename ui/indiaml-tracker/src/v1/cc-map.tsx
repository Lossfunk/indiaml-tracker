import React, { useState, useEffect } from 'react';
import ChoroplethMap from '@/components/map';

const App = () => {
  const [mapData, setMapData] = useState([]);

  useEffect(() => {
    // Replace this with your data-fetching logic.
    fetch('/api/author-countries')
      .then(response => response.json())
      .then(data => setMapData(data));
  }, []);

  return (
    <div style={{ width: '100%', height: '600px' }}>
      <ChoroplethMap data={mapData} title="Authors by Country" />
    </div>
  );
};

export default App;

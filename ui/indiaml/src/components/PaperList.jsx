import React, { useState, useEffect } from 'react';
import PaperCard from './PaperCard';
import FilterButtons from './FilterButtons';
import papersData from '../assets/data/neurips-2024-india-author-data.json'; // Ensure the path is correct

const PapersList = () => {
  const [filter, setFilter] = useState('none');
  const [filteredPapers, setFilteredPapers] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Simulate data fetching delay
    const fetchData = async () => {
      setIsLoading(true);
      // Simulate delay
      await new Promise((resolve) => setTimeout(resolve, 500));
      applyFilter(filter);
      setIsLoading(false);
    };

    fetchData();
  }, [filter]);

  const applyFilter = (filterType) => {
    switch (filterType) {
      case 'top_author':
        setFilteredPapers(papersData.filter((paper) => paper.top_author_from_india));
        break;
      case 'majority_authors':
        setFilteredPapers(papersData.filter((paper) => paper.majority_authors_from_india));
        break;
      case 'none':
      default:
        setFilteredPapers(papersData);
        break;
    }
  };

  return (
    <div>
      <FilterButtons onFilter={setFilter} currentFilter={filter} />
      {isLoading ? (
        <p className="text-center text-gray-500">Loading papers...</p>
      ) : filteredPapers.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {filteredPapers.map((paper, index) => (
            <PaperCard key={index} paper={paper} />
          ))}
        </div>
      ) : (
        <p className="text-center text-gray-500">No papers found for the selected filter.</p>
      )}
    </div>
  );
};

export default PapersList;

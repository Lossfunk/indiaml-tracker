import React from 'react';
import { FaFilter } from 'react-icons/fa';

const FilterButtons = ({ onFilter, currentFilter }) => {
  // Define filter options
  const filters = [
    { label: 'Top Author from India', value: 'top_author', icon: <FaFilter /> },
    { label: 'Majority Authors from India', value: 'majority_authors', icon: <FaFilter /> },
    { label: 'All Papers', value: 'none', icon: <FaFilter /> },
  ];

  return (
    <div className="flex flex-wrap gap-4 mb-8">
      {filters.map((filter) => (
        <button
          key={filter.value}
          onClick={() => onFilter(filter.value)}
          className={`flex items-center px-5 py-2 rounded-full border transition-all duration-300 shadow ${
            currentFilter === filter.value
              ? 'bg-primary text-white border-primary hover:bg-primary-dark'
              : 'bg-white text-gray-700 border-gray-300 hover:bg-secondary-light'
          } focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2`}
          aria-pressed={currentFilter === filter.value}
          aria-label={`Filter papers: ${filter.label}`}
        >
          {filter.icon}
          <span className="ml-3">{filter.label}</span>
        </button>
      ))}
    </div>
  );
};

export default FilterButtons;

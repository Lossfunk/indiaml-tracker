import React from 'react';
import { FaGlobe, FaUniversity, FaLink } from 'react-icons/fa'; // Importing icons

const PaperCard = ({ paper }) => {
  // Function to determine if the top author is from India
  const isTopAuthorIndian = paper.top_author_from_india;
  // Function to determine if majority authors are from India
  const areMajorityAuthorsIndian = paper.majority_authors_from_india;

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden transform hover:scale-105 transition-transform duration-300">
      {/* Paper Title */}
      <div className="p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">{paper.paper_title}</h2>
        {/* PDF Link */}
        <a
          href={paper.pdf_url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center text-blue-500 hover:underline mb-4"
        >
          <FaLink className="mr-2" />
          View PDF
        </a>
        {/* Authors */}
        <div className="mt-4">
          <h3 className="text-lg font-semibold text-gray-700 mb-2">Authors:</h3>
          <ul className="space-y-1">
            {paper.author_list.map((author, index) => (
              <li key={index} className="flex items-center">
                {/* Placeholder for Avatar */}
                <div className="w-8 h-8 bg-gray-300 rounded-full mr-2 flex items-center justify-center text-white text-sm">
                  {author.name.charAt(0)}
                </div>
                <span className="text-gray-600">
                  {author.name} ({author.affiliation_country})
                </span>
              </li>
            ))}
          </ul>
        </div>
      </div>
      {/* Badges */}
      <div className="px-6 pb-4 flex space-x-2">
        {isTopAuthorIndian && (
          <span className="bg-green-100 text-green-800 text-sm font-medium px-2.5 py-0.5 rounded">
            Top Author from India
          </span>
        )}
        {areMajorityAuthorsIndian && (
          <span className="bg-yellow-100 text-yellow-800 text-sm font-medium px-2.5 py-0.5 rounded">
            Majority Authors from India
          </span>
        )}
      </div>
    </div>
  );
};

export default PaperCard;

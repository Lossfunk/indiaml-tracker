// src/components/dashboard/InstitutionCard.tsx

import React, { useState, useCallback } from 'react';
import { 
  FaFileAlt, 
  FaUsers, 
  FaStar, 
  FaTrophy, 
  FaGraduationCap, 
  FaBuilding, 
  FaChevronDown,
  FaUser
} from 'react-icons/fa';
import { InstitutionData } from '../../types/dashboard';
import { TabButton } from '../shared/charts/chart-components';

interface InstitutionCardProps {
  institution: InstitutionData;
  index: number;
}

export const InstitutionCard: React.FC<InstitutionCardProps> = ({
  institution,
  index,
}) => {
  const [isExpanded, setIsExpanded] = useState(index === 0);
  const [activeTab, setActiveTab] = useState<"papers" | "authors">("papers");

  const toggleExpansion = useCallback(() => setIsExpanded((prev) => !prev), []);
  const animationDelay = `${index * 0.05}s`;
  const detailsId = `institution-details-${institution.institute.replace(
    /\s+/g,
    "-"
  )}-${index}`;

  return (
    <div
      className="bg-card rounded-lg shadow-md overflow-hidden mb-4 mt-8 border border-border hover:border-primary hover:shadow-lg transition-all duration-300 animate-fade-in"
      style={{ animationDelay, opacity: 0, animationFillMode: "forwards" }}
    >
      <div
        className="p-4 cursor-pointer flex justify-between items-center"
        onClick={toggleExpansion}
        role="button"
        aria-expanded={isExpanded}
        aria-controls={detailsId}
      >
        <div className="flex-1 mr-4 overflow-hidden">
          <h3
            className="text-card-foreground text-3xl pb-5 truncate font-semibold"
            title={institution.institute}
          >
            {institution.institute}
          </h3>
          <div className="flex items-center flex-wrap text-sm text-muted-foreground mt-1 space-x-4 gap-y-2">
            <span className="flex items-center whitespace-nowrap">
              <FaFileAlt className="mr-1.5 text-blue-500 dark:text-blue-400 flex-shrink-0" />
              <span className="text-blue-500 dark:text-blue-400 font-medium">
                {Math.max(institution.total_paper_count, institution.unique_paper_count)}
              </span>
              &nbsp;{Math.max(institution.total_paper_count, institution.unique_paper_count) === 1 ? "Paper" : "Papers"}
            </span>
            <span className="flex items-center whitespace-nowrap">
              <FaUsers className="mr-1.5 text-pink-500 dark:text-pink-400 flex-shrink-0" />
              <span className="text-pink-500 dark:text-pink-400 font-medium">
                {institution.author_count}
              </span>
              &nbsp;{institution.author_count === 1 ? "Author" : "Authors"}
            </span>
            {institution.spotlights > 0 && (
              <span className="flex items-center whitespace-nowrap">
                <FaStar className="mr-1.5 text-yellow-500 dark:text-yellow-400 flex-shrink-0" size={14} />
                {institution.spotlights}{" "}
                {institution.spotlights === 1 ? "Spotlight" : "Spotlights"}
              </span>
            )}
            {institution.orals > 0 && (
              <span className="flex items-center whitespace-nowrap">
                <FaTrophy className="mr-1.5 text-emerald-500 dark:text-emerald-400 flex-shrink-0" size={14} />
                {institution.orals} {institution.orals === 1 ? "Oral" : "Orals"}
              </span>
            )}
            <span className="flex items-center whitespace-nowrap capitalize">
              {institution.type === "academic" ? (
                <FaGraduationCap className="mr-1.5 text-blue-500 dark:text-blue-400 flex-shrink-0" />
              ) : (
                <FaBuilding className="mr-1.5 text-pink-500 dark:text-pink-400 flex-shrink-0" />
              )}{" "}
              {institution.type}
            </span>
          </div>
        </div>
        <div
          className={`transform transition-transform duration-300 flex-shrink-0 ${
            isExpanded ? "rotate-180" : ""
          }`}
        >
          <FaChevronDown className="w-5 h-5 text-muted-foreground" />
        </div>
      </div>
      {isExpanded && (
        <div id={detailsId} className="border-t border-border">
          <div className="flex border-b border-border px-4 pt-3 bg-muted/30">
            <TabButton
              active={activeTab === "papers"}
              onClick={() => setActiveTab("papers")}
              icon={<FaFileAlt className="text-blue-500" size={14} />}
            >
              Papers ({institution.unique_paper_count})
            </TabButton>
            <TabButton
              active={activeTab === "authors"}
              onClick={() => setActiveTab("authors")}
              icon={<FaUser className="text-pink-500" size={14} />}
            >
              Authors ({institution.author_count})
            </TabButton>
          </div>
          <div className="px-4 pb-4 pt-3">
            {activeTab === "papers" && (
              <div>
                {institution.papers && institution.papers.length > 0 ? (
                  <ul className="space-y-2 max-h-60 overflow-y-auto pr-2 custom-scrollbar">
                    {institution.papers.map((paper, idx) => (
                      <li
                        key={`${paper.id}-${idx}`}
                        className="text-muted-foreground text-sm bg-background p-3 rounded-md shadow-sm transition-all duration-200 hover:shadow-md"
                      >
                        <a
                          href={`https://openreview.net/forum?id=${paper.id}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="hover:text-primary transition-colors block break-words"
                          title={paper.title}
                        >
                          {paper.title}{" "}
                          <span className="text-xs text-muted-foreground/70 ml-1">
                            (ID: {paper.id})
                          </span>
                        </a>
                        {paper.isSpotlight && (
                          <span className="ml-2 mt-1 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300 shadow-sm">
                            <FaStar className="mr-1" size={10} />
                            Spotlight
                          </span>
                        )}
                        {paper.isOral && (
                          <span className="ml-2 mt-1 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-300 shadow-sm">
                            <FaTrophy className="mr-1" size={10} />
                            Oral
                          </span>
                        )}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-muted-foreground/70 text-sm italic py-3">
                    No specific paper details available.
                  </p>
                )}
              </div>
            )}
            {activeTab === "authors" && (
              <div>
                {institution.authors && institution.authors.length > 0 ? (
                  <ul className="space-y-1.5 max-h-60 overflow-y-auto pr-2 custom-scrollbar text-sm text-muted-foreground">
                    {institution.authors.map((author, idx) => (
                      <li
                        key={`author-${idx}`}
                        className="flex items-center bg-background p-2.5 rounded-md hover:bg-muted/30 transition-colors duration-200"
                      >
                        <FaUser
                          className="mr-2 text-pink-400 flex-shrink-0"
                          size={12}
                        />
                        <span>{author}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-muted-foreground/70 text-sm italic py-3">
                    Author details not available.
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

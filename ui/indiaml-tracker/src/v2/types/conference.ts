/**
 * Weights assigned to different paper statuses (oral, spotlight, etc.).
 */
export type StatusWeights = {
  oral: number;
  spotlight: number;
  poster: number;
  unknown: number;
};

/**
 * Configuration settings used for data processing and scoring.
 */
export type Config = {
  first_author_weight: number;
  last_author_weight: number;
  middle_author_weight: number;
  status_weights: StatusWeights;
  output_format: string;
  include_review_details: boolean;
  include_citation_data: boolean;
};

/**
 * Information about one of the authors of the paper.
 */
export type Author = {
  /** A unique identifier for the author. */
  id: string;
  /** The full name of the author. */
  name: string;
  /** Author names as displayed on the site, potentially including all authors. */
  name_site?: string | null;
  /** The author's ID on OpenReview. */
  openreview_id: string;
  /** The author's position in the author list (1-indexed). */
  position: number;
  /** The gender of the author. */
  gender?: "M" | "F" | null;
  /** URL to the author's personal homepage. */
  homepage_url?: string | null;
  /** The author's ID on DBLP. */
  dblp_id?: string | null;
  /** The author's ID for Google Scholar. */
  google_scholar_url?: string | null;
  /** The author's ORCID ID. */
  orcid?: string | null;
  /** The author's LinkedIn profile URL slug. */
  linkedin_url?: string | null;
  twitter_url?: string | null;
  primary_email?: string | null;
  /** The author's institutional affiliation. */
  affiliations?: string | null;
  /** A list of countries associated with the author's affiliation. */
  countries: string[];
  /** A list of country codes (ISO 3166-1 alpha-2) for the affiliations. */
  country_codes: string[];
};

/**
 * Aggregated review and citation data for the paper.
 */
export type Reviews = {
  /** The mean rating from reviewers. */
  rating_mean: number;
  /** The standard deviation of reviewer ratings. */
  rating_std: number;
  /** The mean confidence score from reviewers. */
  confidence_mean: number;
  /** The standard deviation of reviewer confidence scores. */
  confidence_std: number;
  total_reviews?: number | null;
  total_reviewers?: number | null;
  /** The number of citations according to Google Scholar. */
  google_scholar_citations: number;
  /** The number of citations according to Semantic Scholar. */
  semantic_scholar_citations: number;
};

/**
 * Represents a single paper from the conference.
 */
export type Paper = {
  /** Unique identifier for the paper. */
  paper_id: string;
  /** The title of the paper. */
  title: string;
  /** The acceptance status of the paper (e.g., Oral, Poster). */
  status: "Spotlight" | "Poster" | "Oral" | "Reject" | "Withdraw";
  /** The normalized, lowercase status of the paper. */
  normalized_status: "spotlight" | "poster" | "oral" | "rejected" | "withdrawn";
  /** The abstract of the paper. */
  abstract: string;
  /** A short summary of the paper (Too Long; Didn't Read). */
  tldr?: string;
  /** URL to the paper's page on the conference website. */
  site_url: string;
  /** URL to the PDF of the paper. */
  pdf_url?: string | null;
  /** URL to the GitHub repository for the paper. */
  github_url?: string;
  /** The total number of authors for the paper. */
  total_authors: number;
  /** The conference track the paper was submitted to. */
  track_name: string;
  /** Information about one of the authors of the paper. */
  author: Author;
  /** A calculated score for ranking the paper. */
  sort_score: number;
  /** Aggregated review and citation data for the paper. */
  reviews: Reviews;
};

/**
 * Schema for JSON data representing papers from the ICLR 2021 conference with a focus on India.
 */
export type ConferenceData = {
  /** The name of the conference. */
  conference: string;
  /** The country of focus for the data analysis. */
  focus_country: string;
  /** The total number of papers included in the data. */
  total_papers: number;
  /** The timestamp when the data was generated. */
  generated_at: string;
  /** Configuration settings used for data processing and scoring. */
  config: Config;
  /** A list of papers. */
  papers: Paper[];
};
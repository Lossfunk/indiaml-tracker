export interface Paper {
  id: string;
  title: string;
  paper_id: string;
  author_list: {
    name: string;
    openreview_id: string;
    affiliation_name?: string;
    affiliation_domain?: string;
    affiliation_country?: string;

  }[];
  abstract: string;
  conference: "NeurIPS" | "ICML";
  year: number;
  venue?: "oral" | "poster" | "spotlight";
  paper_content: string;
  paper_title: string;
  accepted_in: string[];
  pdf_url: string;
  top_author_from_india: boolean;
  majority_authors_from_india: boolean;
}

export interface AuthorInfo {
  name: string;
  affiliation: string;
}

export interface Paper {
    id: string
    title: string
    authors: string[]
    abstract: string
    conference: "NeurIPS" | "ICML"
    year: number
  }
  
  export interface AuthorInfo {
    name: string
    affiliation: string
  }
  
  
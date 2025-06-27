# Academic Papers Dataset Schema Documentation

## Overview
This is a document outlining the structure of paperlists json structure (reverse engineered + edited using claude)

**Dataset Structure**: Array of Paper Objects  
**Data Source**: ICML 2025 Conference  
**Record Count**: Variable (sample shows multiple papers)  

## Core Data Schema

### Paper Identification & Metadata
| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `title` | string | Paper title | "Off-Policy Actor-Critic for Adversarial Observation Robustness..." |
| `status` | string | Publication status | "Poster", "Oral", "Spotlight" |
| `track` | string | Conference track | "main", "Position" |
| `site` | string | Conference presentation URL | "https://icml.cc/virtual/2025/poster/46516" |
| `id` | string | Unique paper identifier | "3vjsUgCsZ4" |
| `tldr` | string | Brief summary (often empty) | "" |
| `abstract` | string | Paper abstract | "Recently, robust reinforcement learning..." |
| `keywords` | string | Semicolon-separated keywords | "Reinforcement Learning;Deep Learning;Adversarial Learning" |
| `primary_area` | string | Primary research area | "reinforcement_learning" |
| `supplementary_material` | string | Supplementary material info (often empty) | "" |
| `bibtex` | string | BibTeX citation format | "@inproceedings{...}" |
| `github` | string | GitHub repository link (often empty) | "" |
| `project` | string | Project page link (often empty) | "" |

### Author Information
| Field | Type | Description | Format Notes |
|-------|------|-------------|--------------|
| `author_site` | string | Author names from site | Semicolon-separated list |
| `author` | string | Standardized author names | Semicolon-separated list |
| `authorids` | string | Author IDs | Semicolon-separated list with ~ prefix |
| `gender` | string | Author genders | "M", "F", "", "Unspecified" (semicolon-separated) |
| `homepage` | string | Author homepages | Semicolon-separated URLs |
| `dblp` | string | DBLP profile IDs | Semicolon-separated |
| `google_scholar` | string | Google Scholar profile URLs | Semicolon-separated |
| `orcid` | string | ORCID identifiers | Semicolon-separated |
| `linkedin` | string | LinkedIn profile URLs | Semicolon-separated |
| `or_profile` | string | OpenReview profile IDs | Semicolon-separated |
| `author_num` | number | Total number of authors | Integer value |

## Affiliation System

### Core Affiliation Fields
| Field | Type | Description | Format Notes |
|-------|------|-------------|--------------|
| `aff` | string | Raw affiliations | **Semicolon-separated; "+" indicates dual affiliations** |
| `aff_domain` | string | Email domains | **Semicolon-separated; "+" for dual domains** |
| `position` | string | Author positions | **Semicolon-separated; "+" for dual positions** |
| `email` | string | Processed email domains | Same pattern as aff_domain |

### Normalized Affiliation Data
| Field | Type | Description | Format Notes |
|-------|------|-------------|--------------|
| `aff_unique_index` | string | Unique affiliation indices | **"+" indicates mapping to multiple institutions** |
| `aff_unique_norm` | string | Normalized unique affiliations | Semicolon-separated clean names |
| `aff_unique_dep` | string | Departments | Semicolon-separated |
| `aff_unique_url` | string | Institution URLs | Semicolon-separated |
| `aff_unique_abbr` | string | Institution abbreviations | Semicolon-separated |

### Geographic Information
| Field | Type | Description | Format Notes |
|-------|------|-------------|--------------|
| `aff_campus_unique_index` | string | Campus indices | Semicolon-separated |
| `aff_campus_unique` | string | Campus names | Semicolon-separated |
| `aff_country_unique_index` | string | Country indices | **"+" for authors with multi-country affiliations** |
| `aff_country_unique` | string | Country names | Semicolon-separated |

### Dual Affiliation System ("+")

The dataset uses a **"+" delimiter** to represent authors with multiple institutional affiliations:

#### Pattern Rules
- **Semicolons (;)**: Separate different authors
- **Plus signs (+)**: Indicate multiple affiliations for the same author
- **Consistent indexing**: All affiliation fields maintain the same author order

#### Example: Multi-Institutional Author
```json
{
  "aff": "McGill University;Borealis AI;Wayve;Google DeepMind+McGill University;University of Montreal",
  "aff_domain": "mail.mcgill.ca;borealisai.com;wayve.ai;google.com+mcgill.ca;umontreal.ca",
  "aff_unique_index": "0;1;2;3+0;4",
  "position": "PhD student;Researcher;Principal Researcher;Research Team Lead+Associate Professor;Full Professor"
}
```


**Interpretation**: The 4th author has dual affiliation (Google DeepMind + McGill University) with dual roles (Research Team Lead + Associate Professor).

## Review Process Data

### Basic Review Information
| Field | Type | Description | Format |
|-------|------|-------------|---------|
| `reviewers` | string | Reviewer identifiers | Semicolon-separated IDs |
| `pdf_size` | number | PDF file size | Always 0 in this dataset |
| `recommendation` | string | Reviewer recommendations | Semicolon-separated numbers (1-5 scale) |

### Review Metrics (Position Papers)
| Field | Type | Description | Scale |
|-------|------|-------------|-------|
| `rating` | string | Overall ratings | 1-5 scale (semicolon-separated) |
| `confidence` | string | Reviewer confidence | 1-5 scale (semicolon-separated) |
| `support` | string | Support scores | 1-5 scale (semicolon-separated) |
| `significance` | string | Significance scores | 1-5 scale (semicolon-separated) |
| `discussion_potential` | string | Discussion potential | 1-5 scale (semicolon-separated) |
| `argument_clarity` | string | Argument clarity | 1-5 scale (semicolon-separated) |
| `related_work` | string | Related work quality | 1-5 scale (semicolon-separated) |

### Word Count Metrics
All word count fields follow the pattern `wc_[category]` with semicolon-separated counts:

| Field | Description |
|-------|-------------|
| `wc_summary` | Word counts in summaries |
| `wc_strengths_and_weaknesses` | Word counts in strengths/weaknesses sections |
| `wc_questions` | Word counts in questions sections |
| `wc_review` | Total review word counts |
| `wc_reply_reviewers` | Word counts in reviewer replies |
| `wc_reply_authors` | Word counts in author replies |
| `wc_claims_and_evidence` | Word counts in claims/evidence |
| `wc_methods_and_evaluation` | Word counts in methods/evaluation |
| `wc_theoretical_claims` | Word counts in theoretical claims |
| `wc_experimental_designs_or_analyses` | Word counts in experimental sections |
| `wc_supplementary_material` | Word counts in supplementary material |
| `wc_relation_to_broader_scientific_literature` | Word counts in literature relation |
| `wc_essential_references_not_discussed` | Word counts in missing references |

### Reply Tracking
| Field | Type | Description | Format |
|-------|------|-------------|---------|
| `reply_reviewers` | string | Number of reviewer replies | Semicolon-separated numbers |
| `reply_authors` | string | Number of author replies | Semicolon-separated numbers |

## Statistical Aggregations

All average fields contain arrays of `[mean, standard_deviation]`:

### Review Score Averages
| Field | Type | Description |
|-------|------|-------------|
| `rating_avg` | [number, number] | [mean_rating, std_dev] |
| `confidence_avg` | [number, number] | [mean_confidence, std_dev] |
| `support_avg` | [number, number] | [mean_support, std_dev] |
| `significance_avg` | [number, number] | [mean_significance, std_dev] |
| `discussion_potential_avg` | [number, number] | [mean_discussion_potential, std_dev] |
| `argument_clarity_avg` | [number, number] | [mean_argument_clarity, std_dev] |
| `related_work_avg` | [number, number] | [mean_related_work, std_dev] |

### Word Count Averages
All `wc_*_avg` fields follow the same `[mean, std_dev]` pattern:
- `wc_summary_avg`, `wc_review_avg`, `wc_questions_avg`, etc.

### Other Averages
| Field | Type | Description |
|-------|------|-------------|
| `replies_avg` | [number, number] | [mean_replies, std_dev] |
| `authors#_avg` | [number, number] | [mean_authors, std_dev] |

### Correlation Metrics
| Field | Type | Description | Notes |
|-------|------|-------------|-------|
| `corr_rating_confidence` | number | Correlation between rating and confidence | Only present for some papers |

## External Links & Citations

### Citation Data
| Field | Type | Description | Special Values |
|-------|------|-------------|----------------|
| `gs_citation` | number | Google Scholar citation count | -1 if unavailable |
| `gs_cited_by_link` | string | Google Scholar "cited by" URL | "" if unavailable |
| `gs_version_total` | number | Total versions on Google Scholar | -1 if unavailable |

### Platform Links
| Field | Type | Description | Pattern |
|-------|------|-------------|---------|
| `openreview` | string | OpenReview page URL | "https://openreview.net/forum?id=..." |
| `pdf` | string | PDF download URL | "https://openreview.net/pdf?id=..." |

## Data Quality Notes

### Missing Value Conventions
- **Strings**: Empty strings `""` for missing text data
- **Numbers**: `-1` for missing numeric values (citations, versions)
- **Arrays**: Empty arrays `[]` or zero-filled arrays where applicable

### Consistency Rules
1. **Field Ordering**: Author-related fields maintain consistent ordering across semicolon-separated values
2. **Dual Affiliations**: "+" delimiter consistently used across all affiliation fields for the same author
3. **URL Patterns**: Most URLs follow predictable patterns (OpenReview, ICML virtual conference)
4. **Numeric Scales**: Review scores typically use 1-5 scales

### Data Integrity
- All papers have unique `id` values
- Author count in `author_num` matches the number of semicolon-separated entries in author fields
- Affiliation indices in `aff_unique_index` map correctly to `aff_unique_norm`

## Use Cases

This dataset enables analysis across multiple dimensions:

### Academic Collaboration
- **Co-authorship networks**: Using author and affiliation data
- **Institutional collaboration patterns**: Via dual affiliation analysis
- **Geographic research distribution**: Through country and campus data

### Review Process Analysis
- **Peer review bias studies**: Using reviewer scores and word counts
- **Review quality metrics**: Via word count distributions and reply patterns
- **Conference acceptance patterns**: Through status and recommendation data

### Research Trends
- **Topic evolution**: Via keywords and primary_area fields
- **Citation impact**: Through Google Scholar metrics
- **Research area distributions**: Across institutions and countries

### Career & Mobility Studies
- **Academic career progression**: Via position and affiliation changes
- **Industry-academia transitions**: Through dual affiliation patterns
- **International collaboration**: Via multi-country affiliations

## Example Record Structure

```json
{
  "title": "Off-Policy Actor-Critic for Adversarial Observation Robustness",
  "status": "Poster",
  "track": "main",
  "id": "3vjsUgCsZ4",
  "author": "Kosuke Nakanishi;Akihiro Kubo;Yuji Yasui;Shin Ishii",
  "aff": ";Kyoto University;Honda R&D Co., Ltd.;Kyoto University",
  "aff_unique_index": "0;1;2;1",
  "aff_unique_norm": ";Kyoto University;Honda R&D Co., Ltd.",
  "position": ";PhD student;Principal Researcher;Full Professor",
  "rating_avg": [3.0, 0.0],
  "author_num": 4,
  "gs_citation": -1,
  "openreview": "https://openreview.net/forum?id=3vjsUgCsZ4"
}
```

This comprehensive schema documentation provides the foundation for effective analysis and utilization of the academic papers dataset.
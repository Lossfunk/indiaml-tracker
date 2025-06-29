# Common Database Queries for IndiaML v2

This document provides a collection of commonly used SQL queries for analyzing academic paper data in the IndiaML v2 database.

## Table of Contents
1. [Paper Analytics](#paper-analytics)
2. [Author Analytics](#author-analytics)
3. [Institution Analytics](#institution-analytics)
4. [Conference Analytics](#conference-analytics)
5. [Review Analytics](#review-analytics)
6. [Citation Analytics](#citation-analytics)
7. [Collaboration Networks](#collaboration-networks)
8. [Geographic Analysis](#geographic-analysis)

## Paper Analytics

### Top Papers by Citation Count
```sql
SELECT 
    p.id,
    p.title,
    p.status,
    c.google_scholar_citations,
    conf.name as conference,
    conf.year
FROM papers p
JOIN citations c ON p.id = c.paper_id
JOIN tracks t ON p.track_id = t.id
JOIN conferences conf ON t.conference_id = conf.id
ORDER BY c.google_scholar_citations DESC
LIMIT 50;
```

### Papers by Research Area
```sql
SELECT 
    primary_area,
    COUNT(*) as paper_count,
    AVG(author_count) as avg_authors,
    COUNT(DISTINCT pa.author_id) as unique_authors
FROM papers p
LEFT JOIN paper_authors pa ON p.id = pa.paper_id
WHERE primary_area IS NOT NULL
GROUP BY primary_area
ORDER BY paper_count DESC;
```

### Papers with GitHub Repositories
```sql
SELECT 
    p.id,
    p.title,
    p.github_url,
    c.google_scholar_citations,
    conf.name as conference
FROM papers p
LEFT JOIN citations c ON p.id = c.paper_id
JOIN tracks t ON p.track_id = t.id
JOIN conferences conf ON t.conference_id = conf.id
WHERE p.github_url IS NOT NULL AND p.github_url != ''
ORDER BY c.google_scholar_citations DESC;
```

### Paper Status Distribution by Conference
```sql
SELECT 
    conf.name as conference,
    conf.year,
    p.status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY conf.name, conf.year), 2) as percentage
FROM papers p
JOIN tracks t ON p.track_id = t.id
JOIN conferences conf ON t.conference_id = conf.id
WHERE p.status IS NOT NULL
GROUP BY conf.name, conf.year, p.status
ORDER BY conf.name, conf.year, count DESC;
```

## Author Analytics

### Most Prolific Authors
```sql
SELECT 
    a.name,
    a.orcid,
    COUNT(DISTINCT pa.paper_id) as paper_count,
    COUNT(DISTINCT CASE WHEN pa.author_order = 1 THEN pa.paper_id END) as first_author_count,
    STRING_AGG(DISTINCT conf.name, ', ') as conferences
FROM authors a
JOIN paper_authors pa ON a.id = pa.author_id
JOIN papers p ON pa.paper_id = p.id
JOIN tracks t ON p.track_id = t.id
JOIN conferences conf ON t.conference_id = conf.id
GROUP BY a.id, a.name, a.orcid
HAVING paper_count >= 3
ORDER BY paper_count DESC, first_author_count DESC;
```

### Authors by Institution
```sql
SELECT 
    i.normalized_name as institution,
    c.name as country,
    COUNT(DISTINCT a.id) as author_count,
    COUNT(DISTINCT pa.paper_id) as paper_count,
    ROUND(AVG(cit.google_scholar_citations), 2) as avg_citations
FROM institutions i
JOIN countries c ON i.country_id = c.id
JOIN affiliations af ON i.id = af.institution_id
JOIN authors a ON af.author_id = a.id
JOIN paper_authors pa ON a.id = pa.author_id
LEFT JOIN citations cit ON pa.paper_id = cit.paper_id
GROUP BY i.id, i.normalized_name, c.name
HAVING author_count >= 5
ORDER BY paper_count DESC;
```

### Author Collaboration Network
```sql
-- Find authors who have collaborated (co-authored papers)
SELECT 
    a1.name as author1,
    a2.name as author2,
    COUNT(*) as collaboration_count,
    STRING_AGG(p.title, '; ') as papers
FROM paper_authors pa1
JOIN paper_authors pa2 ON pa1.paper_id = pa2.paper_id AND pa1.author_id < pa2.author_id
JOIN authors a1 ON pa1.author_id = a1.id
JOIN authors a2 ON pa2.author_id = a2.id
JOIN papers p ON pa1.paper_id = p.id
GROUP BY a1.id, a1.name, a2.id, a2.name
HAVING collaboration_count >= 2
ORDER BY collaboration_count DESC;
```

### Authors with Multiple Affiliations
```sql
SELECT 
    a.name,
    a.orcid,
    COUNT(DISTINCT af.institution_id) as institution_count,
    STRING_AGG(i.normalized_name, '; ') as institutions,
    STRING_AGG(DISTINCT c.name, '; ') as countries
FROM authors a
JOIN affiliations af ON a.id = af.author_id
JOIN institutions i ON af.institution_id = i.id
JOIN countries c ON i.country_id = c.id
GROUP BY a.id, a.name, a.orcid
HAVING institution_count > 1
ORDER BY institution_count DESC;
```

## Institution Analytics

### Top Institutions by Paper Count
```sql
SELECT 
    i.normalized_name as institution,
    c.name as country,
    COUNT(DISTINCT pa.paper_id) as paper_count,
    COUNT(DISTINCT a.id) as author_count,
    ROUND(AVG(cit.google_scholar_citations), 2) as avg_citations,
    SUM(cit.google_scholar_citations) as total_citations
FROM institutions i
JOIN countries c ON i.country_id = c.id
JOIN affiliations af ON i.id = af.institution_id
JOIN authors a ON af.author_id = a.id
JOIN paper_authors pa ON a.id = pa.author_id
LEFT JOIN citations cit ON pa.paper_id = cit.paper_id
GROUP BY i.id, i.normalized_name, c.name
ORDER BY paper_count DESC
LIMIT 50;
```

### Institution Rankings by Conference
```sql
SELECT 
    conf.name as conference,
    conf.year,
    i.normalized_name as institution,
    c.name as country,
    COUNT(DISTINCT pa.paper_id) as paper_count,
    RANK() OVER (PARTITION BY conf.name, conf.year ORDER BY COUNT(DISTINCT pa.paper_id) DESC) as rank
FROM institutions i
JOIN countries c ON i.country_id = c.id
JOIN affiliations af ON i.id = af.institution_id
JOIN authors a ON af.author_id = a.id
JOIN paper_authors pa ON a.id = pa.author_id
JOIN papers p ON pa.paper_id = p.id
JOIN tracks t ON p.track_id = t.id
JOIN conferences conf ON t.conference_id = conf.id
GROUP BY conf.name, conf.year, i.id, i.normalized_name, c.name
HAVING paper_count >= 3
ORDER BY conf.name, conf.year, rank;
```

### Institution Collaboration Matrix
```sql
-- Find institutions that collaborate (authors from different institutions on same paper)
SELECT 
    i1.normalized_name as institution1,
    i2.normalized_name as institution2,
    c1.name as country1,
    c2.name as country2,
    COUNT(DISTINCT p.id) as collaborative_papers
FROM papers p
JOIN paper_authors pa1 ON p.id = pa1.paper_id
JOIN paper_authors pa2 ON p.id = pa2.paper_id
JOIN authors a1 ON pa1.author_id = a1.id
JOIN authors a2 ON pa2.author_id = a2.id
JOIN affiliations af1 ON a1.id = af1.author_id
JOIN affiliations af2 ON a2.id = af2.author_id
JOIN institutions i1 ON af1.institution_id = i1.id
JOIN institutions i2 ON af2.institution_id = i2.id
JOIN countries c1 ON i1.country_id = c1.id
JOIN countries c2 ON i2.country_id = c2.id
WHERE i1.id < i2.id  -- Avoid duplicates
GROUP BY i1.id, i1.normalized_name, i2.id, i2.normalized_name, c1.name, c2.name
HAVING collaborative_papers >= 3
ORDER BY collaborative_papers DESC;
```

## Conference Analytics

### Conference Statistics by Year
```sql
SELECT 
    name as conference,
    year,
    COUNT(DISTINCT p.id) as total_papers,
    COUNT(DISTINCT pa.author_id) as unique_authors,
    COUNT(DISTINCT i.id) as unique_institutions,
    COUNT(DISTINCT co.id) as unique_countries,
    ROUND(AVG(p.author_count), 2) as avg_authors_per_paper
FROM conferences conf
JOIN tracks t ON conf.id = t.conference_id
JOIN papers p ON t.id = p.track_id
JOIN paper_authors pa ON p.id = pa.paper_id
JOIN authors a ON pa.author_id = a.id
JOIN affiliations af ON a.id = af.author_id
JOIN institutions i ON af.institution_id = i.id
JOIN countries co ON i.country_id = co.id
GROUP BY conf.name, conf.year
ORDER BY conf.name, conf.year;
```

### Track Analysis
```sql
SELECT 
    conf.name as conference,
    conf.year,
    t.track_type,
    t.name as track_name,
    COUNT(p.id) as paper_count,
    ROUND(AVG(rs.rating_mean), 2) as avg_rating,
    ROUND(AVG(cit.google_scholar_citations), 2) as avg_citations
FROM conferences conf
JOIN tracks t ON conf.id = t.conference_id
LEFT JOIN papers p ON t.id = p.track_id
LEFT JOIN review_statistics rs ON p.id = rs.paper_id
LEFT JOIN citations cit ON p.id = cit.paper_id
GROUP BY conf.name, conf.year, t.track_type, t.name
ORDER BY conf.name, conf.year, paper_count DESC;
```

## Review Analytics

### Papers with Highest Review Scores
```sql
SELECT 
    p.id,
    p.title,
    rs.rating_mean,
    rs.confidence_mean,
    rs.total_reviews,
    conf.name as conference,
    conf.year
FROM papers p
JOIN review_statistics rs ON p.id = rs.paper_id
JOIN tracks t ON p.track_id = t.id
JOIN conferences conf ON t.conference_id = conf.id
WHERE rs.total_reviews >= 3
ORDER BY rs.rating_mean DESC, rs.confidence_mean DESC
LIMIT 50;
```

### Review Score Distribution
```sql
SELECT 
    conf.name as conference,
    conf.year,
    ROUND(rs.rating_mean, 1) as rating_bucket,
    COUNT(*) as paper_count,
    ROUND(AVG(rs.confidence_mean), 2) as avg_confidence
FROM review_statistics rs
JOIN papers p ON rs.paper_id = p.id
JOIN tracks t ON p.track_id = t.id
JOIN conferences conf ON t.conference_id = conf.id
WHERE rs.rating_mean IS NOT NULL
GROUP BY conf.name, conf.year, ROUND(rs.rating_mean, 1)
ORDER BY conf.name, conf.year, rating_bucket;
```

### Controversial Papers (High Rating Variance)
```sql
SELECT 
    p.id,
    p.title,
    rs.rating_mean,
    rs.rating_std,
    rs.total_reviews,
    conf.name as conference
FROM papers p
JOIN review_statistics rs ON p.id = rs.paper_id
JOIN tracks t ON p.track_id = t.id
JOIN conferences conf ON t.conference_id = conf.id
WHERE rs.rating_std > 1.0 AND rs.total_reviews >= 3
ORDER BY rs.rating_std DESC;
```

## Citation Analytics

### Most Cited Papers by Conference
```sql
SELECT 
    conf.name as conference,
    conf.year,
    p.title,
    c.google_scholar_citations,
    STRING_AGG(a.name, '; ') as authors
FROM papers p
JOIN citations c ON p.id = c.paper_id
JOIN tracks t ON p.track_id = t.id
JOIN conferences conf ON t.conference_id = conf.id
JOIN paper_authors pa ON p.id = pa.paper_id
JOIN authors a ON pa.author_id = a.id
GROUP BY conf.name, conf.year, p.id, p.title, c.google_scholar_citations
ORDER BY conf.name, conf.year, c.google_scholar_citations DESC;
```

### Citation vs Review Score Correlation
```sql
SELECT 
    conf.name as conference,
    COUNT(*) as paper_count,
    ROUND(AVG(c.google_scholar_citations), 2) as avg_citations,
    ROUND(AVG(rs.rating_mean), 2) as avg_rating,
    -- Calculate correlation coefficient (simplified)
    ROUND(
        (COUNT(*) * SUM(c.google_scholar_citations * rs.rating_mean) - 
         SUM(c.google_scholar_citations) * SUM(rs.rating_mean)) /
        SQRT((COUNT(*) * SUM(c.google_scholar_citations * c.google_scholar_citations) - 
              SUM(c.google_scholar_citations) * SUM(c.google_scholar_citations)) *
             (COUNT(*) * SUM(rs.rating_mean * rs.rating_mean) - 
              SUM(rs.rating_mean) * SUM(rs.rating_mean))), 3
    ) as citation_rating_correlation
FROM papers p
JOIN citations c ON p.id = c.paper_id
JOIN review_statistics rs ON p.id = rs.paper_id
JOIN tracks t ON p.track_id = t.id
JOIN conferences conf ON t.conference_id = conf.id
WHERE c.google_scholar_citations > 0 AND rs.rating_mean IS NOT NULL
GROUP BY conf.name
HAVING paper_count >= 10
ORDER BY citation_rating_correlation DESC;
```

## Collaboration Networks

### International Collaborations
```sql
SELECT 
    c1.name as country1,
    c2.name as country2,
    COUNT(DISTINCT p.id) as collaborative_papers,
    COUNT(DISTINCT a1.id) as authors_country1,
    COUNT(DISTINCT a2.id) as authors_country2
FROM papers p
JOIN paper_authors pa1 ON p.id = pa1.paper_id
JOIN paper_authors pa2 ON p.id = pa2.paper_id
JOIN authors a1 ON pa1.author_id = a1.id
JOIN authors a2 ON pa2.author_id = a2.id
JOIN affiliations af1 ON a1.id = af1.author_id
JOIN affiliations af2 ON a2.id = af2.author_id
JOIN institutions i1 ON af1.institution_id = i1.id
JOIN institutions i2 ON af2.institution_id = i2.id
JOIN countries c1 ON i1.country_id = c1.id
JOIN countries c2 ON i2.country_id = c2.id
WHERE c1.id < c2.id  -- Avoid duplicates
GROUP BY c1.name, c2.name
HAVING collaborative_papers >= 5
ORDER BY collaborative_papers DESC;
```

### Cross-Institution Author Mobility
```sql
-- Authors who have changed institutions
SELECT 
    a.name,
    COUNT(DISTINCT af.institution_id) as institution_count,
    STRING_AGG(
        i.normalized_name || ' (' || c.name || ')', 
        ' → ' ORDER BY af.created_at
    ) as institution_path
FROM authors a
JOIN affiliations af ON a.id = af.author_id
JOIN institutions i ON af.institution_id = i.id
JOIN countries c ON i.country_id = c.id
GROUP BY a.id, a.name
HAVING institution_count > 1
ORDER BY institution_count DESC;
```

## Geographic Analysis

### Papers by Country
```sql
SELECT 
    c.name as country,
    COUNT(DISTINCT p.id) as paper_count,
    COUNT(DISTINCT a.id) as author_count,
    COUNT(DISTINCT i.id) as institution_count,
    ROUND(AVG(cit.google_scholar_citations), 2) as avg_citations
FROM countries c
JOIN institutions i ON c.id = i.country_id
JOIN affiliations af ON i.id = af.institution_id
JOIN authors a ON af.author_id = a.id
JOIN paper_authors pa ON a.id = pa.author_id
JOIN papers p ON pa.paper_id = p.id
LEFT JOIN citations cit ON p.id = cit.paper_id
GROUP BY c.id, c.name
ORDER BY paper_count DESC;
```

### Regional Conference Participation
```sql
SELECT 
    conf.name as conference,
    conf.year,
    c.name as country,
    COUNT(DISTINCT p.id) as paper_count,
    ROUND(
        COUNT(DISTINCT p.id) * 100.0 / 
        SUM(COUNT(DISTINCT p.id)) OVER (PARTITION BY conf.name, conf.year), 
        2
    ) as percentage
FROM conferences conf
JOIN tracks t ON conf.id = t.conference_id
JOIN papers p ON t.id = p.track_id
JOIN paper_authors pa ON p.id = pa.paper_id
JOIN authors a ON pa.author_id = a.id
JOIN affiliations af ON a.id = af.author_id
JOIN institutions i ON af.institution_id = i.id
JOIN countries c ON i.country_id = c.id
GROUP BY conf.name, conf.year, c.name
HAVING paper_count >= 3
ORDER BY conf.name, conf.year, paper_count DESC;
```

## Performance Tips

### Query Optimization
1. **Use indexes**: Most queries above leverage the existing indexes
2. **Limit results**: Add `LIMIT` clauses for large datasets
3. **Filter early**: Use `WHERE` clauses to reduce data before joins
4. **Use EXPLAIN**: Analyze query execution plans for optimization

### Common Patterns
```sql
-- Always join through proper relationships
-- Papers → Tracks → Conferences (for conference info)
-- Authors → Affiliations → Institutions → Countries (for geographic info)
-- Papers → PaperAuthors → Authors (for author info)

-- Use LEFT JOIN for optional relationships (citations, reviews)
-- Use INNER JOIN for required relationships

-- Group by all non-aggregate columns in SELECT
-- Use HAVING for filtering aggregated results
```

### Index Usage Examples
```sql
-- These queries will use indexes efficiently:
SELECT * FROM papers WHERE status = 'Oral';  -- Uses idx_paper_status
SELECT * FROM authors WHERE orcid = '0000-0000-0000-0000';  -- Uses idx_author_orcid
SELECT * FROM institutions WHERE normalized_name = 'MIT';  -- Uses idx_institution_normalized_name

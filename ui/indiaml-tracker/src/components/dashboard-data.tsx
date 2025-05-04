export const dashboardData = {
  conferenceInfo: {
    name: "ICLR",
    year: 2025,
    track: "Conference",
    totalAcceptedPapers: 3705,
  },
  globalStats: {
    // Raw country data as it would come from an API
    countries: [
      {
        affiliation_country: "US",
        paper_count: 1929,
        author_count: 5800,
        spotlights: 65,
        orals: 42,
      },
      {
        affiliation_country: "CN",
        paper_count: 1308,
        author_count: 4500,
        spotlights: 40,
        orals: 25,
      },
      {
        affiliation_country: "HK",
        paper_count: 294,
        author_count: 900,
        spotlights: 10,
        orals: 6,
      },
      // Combined UK/GB - Note: The processing logic will handle mapping 'GB' and 'UK' to 'United Kingdom'
      {
        affiliation_country: "GB",
        paper_count: 293,
        author_count: 880,
        spotlights: 12,
        orals: 7,
      },
      {
        affiliation_country: "UK",
        paper_count: 103,
        author_count: 310,
        spotlights: 4,
        orals: 2,
      }, // Example of separate UK entry before processing
      {
        affiliation_country: "CA",
        paper_count: 255,
        author_count: 750,
        spotlights: 9,
        orals: 5,
      },
      {
        affiliation_country: "SG",
        paper_count: 248,
        author_count: 700,
        spotlights: 8,
        orals: 4,
      },
      {
        affiliation_country: "DE",
        paper_count: 240,
        author_count: 720,
        spotlights: 8,
        orals: 5,
      },
      {
        affiliation_country: "KR",
        paper_count: 187,
        author_count: 550,
        spotlights: 6,
        orals: 3,
      },
      {
        affiliation_country: "CH",
        paper_count: 178,
        author_count: 500,
        spotlights: 7,
        orals: 4,
      },
      {
        affiliation_country: "AU",
        paper_count: 127,
        author_count: 380,
        spotlights: 4,
        orals: 2,
      },
      {
        affiliation_country: "FR",
        paper_count: 120,
        author_count: 350,
        spotlights: 5,
        orals: 2,
      },
      {
        affiliation_country: "JP",
        paper_count: 119,
        author_count: 340,
        spotlights: 4,
        orals: 2,
      },
      {
        affiliation_country: "IL",
        paper_count: 71,
        author_count: 210,
        spotlights: 3,
        orals: 1,
      },
      {
        affiliation_country: "NL",
        paper_count: 70,
        author_count: 200,
        spotlights: 3,
        orals: 1,
      },
      {
        affiliation_country: "IN",
        paper_count: 49,
        author_count: 132,
        spotlights: 2,
        orals: 1,
      },
      // Add more countries if needed
    ],
  },
  indiaFocus: {
    total_indian_authors: 132,
    total_indian_spotlights: 2,
    total_indian_orals: 1,
    institution_types: { academic: 35, corporate: 14 }, // Based on unique papers per institution type
    at_least_one_indian_author: { count: 50, papers: [] }, // Paper lists omitted for brevity in display, but can be populated
    majority_indian_authors: { count: 23, papers: [] },
    first_indian_author: { count: 26, papers: [] },
    institutions: [
      // Ensure 'type' and structure match InstitutionData interface
      {
        institute: "IIT Bombay",
        total_paper_count: 17,
        unique_paper_count: 10,
        author_count: 35,
        spotlights: 1,
        orals: 0,
        type: "academic",
        papers: [
          {
            id: "EzrZX9bd4G",
            title:
              "BEEM: Balanced and Efficient Evaluation Metric for Multi-label Classification with Partially Annotated Labels",
          },
          {
            id: "5pd78GmXC6",
            title:
              "Charting the Path of Quantum Computing towards Foundation Models",
          },
          {
            id: "DFSb67ksVr",
            title: "Clique Guided Cooperative Graph Neural Network Training",
          },
          {
            id: "9h45qxXEx0",
            title:
              "Debiasing Methods in Continual Test-Time Adaptation: What is the Optimal Strategy?",
          },
          {
            id: "NtwFghsJne",
            title:
              "From Search To Recommendation: Progressive Explainable Network",
          },
          {
            id: "k3gCieTXeY",
            title:
              "INCLUDE: Incorporating Linguistic Constraints into Language Models using Diferentiable Logic",
            isSpotlight: true,
          },
          {
            id: "nNiWRRj6r9",
            title:
              "ONLINE: Optimal Sampling from Aggregated Datasets for Molecular Property Prediction",
          },
          {
            id: "l11DZY5Nxu",
            title: "Robust Graph Condensation via Gradient Matching",
          },
          {
            id: "h0vC0fm1q7",
            title:
              "Sensitivity Analysis for Unmeasured Confounding in Causal Mediation Analysis",
          },
          { id: "Q1kPHLUbhi", title: "Towards Self-Improving Vision Models" },
        ],
      },
      {
        institute: "Microsoft Research India",
        total_paper_count: 8,
        unique_paper_count: 6,
        author_count: 20,
        spotlights: 1,
        orals: 1,
        type: "corporate",
        papers: [
          {
            id: "9juyeCqL0u",
            title:
              "Causal Interpretation in the Presence of Latent Variables using Stylized Counterfactuals",
          },
          {
            id: "xkgfLXZ4e0",
            title:
              "Correlating Events and Trends: A Causal Analysis of Temporal Data for Explainable Event Recommendation",
          },
          {
            id: "zl3pfz4VCV",
            title: "MMTEB: A Multi-lingual Multi-task Text Embedding Benchmark",
            isSpotlight: true,
          },
          {
            id: "0dELcFHig2",
            title:
              "Multi-modal Event Causality Analysis: A Novel Task and Benchmark",
          },
          {
            id: "3E8YNv1HjU",
            title:
              "Recite Your References: A New Benchmark and Model for Strong Claim Verification",
            isOral: true,
          },
          {
            id: "l11DZY5Nxu",
            title: "Robust Graph Condensation via Gradient Matching",
          },
        ],
      },
      {
        institute: "Adobe Research India",
        total_paper_count: 7,
        unique_paper_count: 4,
        author_count: 15,
        spotlights: 0,
        orals: 0,
        type: "corporate",
        papers: [
          {
            id: "NHxwxc3ql6",
            title:
              "It Helps to Follow the Crowd: Instruction Following for Improving Persuasiveness",
          },
          {
            id: "TmCcNuo03f",
            title: "Measuring And Improving Engagement in Short Videos",
          },
          {
            id: "NfCEVihkdC",
            title: "Measuring And Improving Persuasiveness in Short Videos",
          },
          {
            id: "ff2V3UR9sC",
            title: "Teaching Human Feedback Preferences to Distilled LLMs",
          },
        ],
      },
      {
        institute: "IIT Delhi",
        total_paper_count: 6,
        unique_paper_count: 3,
        author_count: 12,
        spotlights: 0,
        orals: 0,
        type: "academic",
        papers: [
          {
            id: "5x88lQ2MsH",
            title:
              "Bonsai: Enabling Fast Security Vetting of Closed-Source Applications using Hardware-Assisted Execution and Neural Network guided Fuzzing",
          },
          {
            id: "tDIL7UXmSS",
            title:
              "Quantum Computing for Finance: A Survey of State-of-the-Art Techniques",
          },
          {
            id: "5RZoYIT3u6",
            title:
              "You Only Need One Step: Fast Super-Resolution using Guided Diffusion Model",
          },
        ],
      },
      {
        institute: "IIT Madras",
        total_paper_count: 5,
        unique_paper_count: 3,
        author_count: 10,
        spotlights: 0,
        orals: 0,
        type: "academic",
        papers: [
          {
            id: "ZbkqhKbggH",
            title:
              "ASTrA: A Unified Benchmark for Evaluating Attribute Stealthiness in Face Recognition",
          },
          {
            id: "52UtL8uA35",
            title: "Deep Networks Always Grok and Here is Why",
          },
          {
            id: "qnlG3zPQUy",
            title:
              "ILLUSION: Efficient Hierarchical Parameter Adaptation using Intrinsic Dimension Regression",
          },
        ],
      },
      {
        institute: "IISc Bangalore",
        total_paper_count: 4,
        unique_paper_count: 3,
        author_count: 9,
        spotlights: 0,
        orals: 0,
        type: "academic",
        papers: [
          {
            id: "TfT8i94e1o",
            title:
              "Accelerating Generative Models via Long-Range Dependency Injection",
          },
          {
            id: "2gU1v1K7tT",
            title:
              "Learning from Similar and Dissimilar Data: A Unified Framework for Cross-Domain Adaptation",
          },
          {
            id: "l11DZY5Nxu",
            title: "Robust Graph Condensation via Gradient Matching",
          },
        ], // Example paper data updated
      },
      {
        institute: "Google Research India",
        total_paper_count: 3,
        unique_paper_count: 2,
        author_count: 8,
        spotlights: 0,
        orals: 0,
        type: "corporate",
        papers: [
          {
            id: "TfT8i94e1o",
            title:
              "Accelerating Generative Models via Long-Range Dependency Injection",
          },
          {
            id: "NfCEVihkdC",
            title: "Measuring And Improving Persuasiveness in Short Videos",
          },
        ], // Example paper data updated
      },
      // Add other institutions...
    ],
  },
  interpretations: {
    overview: {
      title: "India's Growth in AI Research at ICLR 2025",
      insights: [
        "India contributed 49 accepted papers to ICLR 2025, representing approximately 1.3% of the total accepted papers (3,705). This places India at rank #16 globally by paper volume.",
        "While significantly behind leaders like the US (1,929 papers) and China (1,308 papers), India's presence signals continued growth in the global AI research landscape.",
        "The inclusion of 2 spotlights and 1 oral presentation (totaling 3 high-visibility papers, or 6.1% of India's contributions) indicates that Indian research is achieving international recognition for quality and impact.",
        "Academic institutions, particularly IITs, form the backbone of India's contribution, though corporate labs like Microsoft Research India demonstrate high impact.",
      ],
      legend:
        "The Global Leaderboard chart shows the top 10 countries by paper count. Longer bars indicate higher research output. India is highlighted in amber for comparison.",
    },
    globalDistribution: {
      title: "Global Research Distribution: Concentration and Gaps",
      insights: [
        "AI research output presented at ICLR 2025 is heavily concentrated. The United States and China together account for over 87% (3,237 out of 3,705) of all accepted papers.",
        "This US-China duopoly underscores their dominant roles in the field but also raises questions about geographic diversity and the potential for echo chambers in research direction.",
        "Beyond the top two, countries like the UK, Hong Kong, Canada, Singapore, Germany, and South Korea form a significant secondary tier, each contributing over 180 papers.",
        "The data highlights opportunities for increased international collaboration to broaden perspectives and potentially accelerate progress by involving researchers from underrepresented regions.",
      ],
      legend:
        "The 'US + China vs Rest' pie chart visually represents the significant share held by the top two countries. The bar chart provides the absolute numbers for comparison.",
    },
    apacContributions: {
      title: "APAC Regional Dynamics: China's Lead and Emerging Hubs",
      insights: [
        "Within the Asia-Pacific (APAC) countries represented, China is the dominant force, contributing 1,308 papers, roughly 76% of the total papers from the selected APAC nations (China, India, HK, SG, JP, KR, AU).",
        "Hong Kong (294 papers) and Singapore (248 papers) show strong performance, particularly relative to their size, positioning themselves as major regional hubs.",
        "South Korea (187 papers), Australia (127 papers), Japan (119 papers), and India (49 papers) follow, each making distinct contributions.",
        "India ranks 7th among these specific APAC countries by paper volume, indicating both its growing participation and the highly competitive nature of the regional AI research landscape.",
      ],
      legend:
        "The APAC Contributions bar chart ranks regional countries by paper count. The accompanying pie chart illustrates the proportion of papers each country contributes within this specific group.",
    },
    indiaFocus: {
      title: "India Focus: Collaboration, Authorship, and Institutions",
      insights: [
        "While 50 papers had at least one author affiliated with an Indian institution, only 23 (46%) had a majority of authors from India. This suggests a high degree of international collaboration, which is beneficial for knowledge exchange.",
        "26 papers (52% of those with Indian authors) listed an Indian-affiliated author first, indicating growing leadership roles, but also room for development in driving research agendas.",
        "Academic institutions contributed the majority of papers (35 papers, ~71%), compared to corporate labs (14 papers, ~29%). This highlights the strength of Indian universities but suggests potential for growth in industrial AI research.",
        "The total number of unique authors affiliated with Indian institutions is 132 across the 49 primary papers.",
      ],
      legend:
        "Authorship charts compare 'Majority Indian' vs 'Minority Indian' contributions and 'First Indian Author' vs 'Non-First'. The Institution Type chart shows the Academic/Corporate split based on paper count.",
    },
    institutionAnalysis: {
      title: "Indian Institutions: Leading Contributors and Impact",
      insights: [
        "IIT Bombay leads among Indian institutions with 10 unique papers, followed by Microsoft Research India (6 papers), Adobe Research India (4 papers), IIT Delhi (3 papers), IIT Madras (3 papers), and IISc Bangalore (3 papers).",
        "While academic institutions dominate in volume (IIT Bombay: 10 papers, 1 spotlight), corporate labs show high impact relative to their output. Microsoft Research India achieved 1 spotlight and 1 oral presentation from its 6 papers.",
        "This suggests different institutional focuses: universities driving broader research exploration and corporate labs potentially concentrating on high-impact, strategically aligned projects.",
        "Geographic concentration is evident, with top institutions primarily located in major hubs like Mumbai, Bangalore, and Delhi.",
      ],
      legend:
        "The 'Papers by Institution' chart ranks the top contributing institutions. The 'Academic vs Corporate' pie chart shows the distribution of papers based on institution type. Colors distinguish academic (blue) and corporate (pink).",
    },
    comparativePerformance: {
      title: "Comparative Performance: India vs. US & China",
      insights: [
        "Direct comparison highlights the scale difference: India (49 papers), US (1,929 papers), China (1,308 papers).",
        "India's spotlight/oral rate (6.1% of its papers) is competitive, comparing favorably to China's (5.0%) and slightly above the US's (5.5%), suggesting high quality within its contributions.",
        "The average number of authors per paper shows variations: India (2.7 authors/paper), US (3.0 authors/paper), China (3.4 authors/paper). This might reflect differences in typical research team sizes, funding levels, or collaboration patterns.",
        "These metrics position India as an emerging research contributor focusing on impactful work, possibly adapting to resource constraints by prioritizing quality and targeted collaborations.",
      ],
      legend:
        "Charts compare absolute paper counts, the number and percentage of spotlights/orals, and the average authors per paper ratio across India, the US, and China.",
    },
    futureOpportunities: {
      title: "Potential Research Focus Areas for India",
      insights: [
        "Analysis of paper titles and inferred topics suggests Indian researchers are actively contributing in areas like Large Language Models (LLMs) & Natural Language Processing (NLP), particularly focusing on evaluation, multilingual aspects, and efficiency.",
        "Graph Neural Networks (GNNs), theoretical foundations of ML (e.g., sampling, representation), and model robustness/efficiency (debiasing, adversarial training, compression) appear as other significant contribution areas.",
        "Leveraging India's linguistic diversity for multilingual NLP and focusing on resource-efficient AI methods could be strategic advantages for future research impact.",
        "These areas align well with global trends but also offer opportunities to address locally relevant challenges that have global implications.",
      ],
      legend:
        "This section qualitatively summarizes observed research themes based on the provided paper data for Indian institutions, highlighting areas of notable activity.",
    },
  },
};

// Type definition for the data structure
export type DashboardData = typeof dashboardData;

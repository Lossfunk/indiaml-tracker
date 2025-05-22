// src/v1/utils/chart-colors.ts

/**
 * Enhanced color palette for conference dashboard charts
 * Provides consistent, visually appealing colors with accessibility in mind
 */

export const chartColors = {
  // Primary colors for main entities
  us: '#4361ee', // Deep blue for US
  cn: '#f72585', // Vivid pink for China
  india: '#ff9e00', // Bright amber for India
  focusCountry: '#ff9e00', // Default focus country color (amber)

  // Semantic colors
  academic: '#4cc9f0', // Light blue for academic institutions
  corporate: '#560bad', // Purple for corporate institutions
  spotlight: '#ffbf47', // Gold for spotlight papers
  oral: '#06d6a0', // Turquoise for oral presentations

  // Chart specific colors
  papers: '#4361ee', // Blue for papers
  authors: '#4895ef', // Lighter blue for authors
  
  // Gradients for multi-series charts
  blueGradient: ['#4361ee', '#4895ef', '#4cc9f0'],
  pinkGradient: ['#f72585', '#b5179e', '#7209b7'],
  amberGradient: ['#ff9e00', '#fb8500', '#f48c06'],
  greenGradient: ['#06d6a0', '#2ec4b6', '#168aad'],
  
  // Chart backgrounds
  chartBackground: 'rgba(255, 255, 255, 0.02)',
  tooltipBackground: 'rgba(250, 250, 255, 0.97)',
  darkTooltipBackground: 'rgba(18, 18, 24, 0.97)',
  
  // Accent/highlight colors
  highlight: '#ffbf47', // Gold highlight
  accent: '#4361ee', // Blue accent
  warning: '#f94144', // Red warning
  
  // Neutral colors
  rest: '#94a3b8', // Slate for "rest of world"
  muted: '#64748b', // Muted text/elements
  grid: 'rgba(203, 213, 225, 0.4)', // Grid lines
  
  // Helper function for generating opacity variants
  withOpacity: (color: string, opacity: number) => {
    // For hex colors
    if (color.startsWith('#')) {
      const r = parseInt(color.slice(1, 3), 16);
      const g = parseInt(color.slice(3, 5), 16);
      const b = parseInt(color.slice(5, 7), 16);
      return `rgba(${r}, ${g}, ${b}, ${opacity})`;
    }
    // For rgba colors
    if (color.startsWith('rgba')) {
      return color.replace(/rgba\((.+?),\s*[\d\.]+\)/, `rgba($1, ${opacity})`);
    }
    // For rgb colors
    if (color.startsWith('rgb')) {
      return color.replace('rgb', 'rgba').replace(')', `, ${opacity})`);
    }
    return color;
  },
  
  // Generate an array of colors for pie/donut charts
  getPieChartColors: (count: number) => {
    const baseColors = [
      '#4361ee', '#f72585', '#ff9e00', '#06d6a0', '#4cc9f0', 
      '#7209b7', '#4895ef', '#f48c06', '#2ec4b6', '#560bad'
    ];
    
    if (count <= baseColors.length) {
      return baseColors.slice(0, count);
    }
    
    // For more colors, create variations of the base colors
    const result = [...baseColors];
    let currentIndex = 0;
    
    while (result.length < count) {
      const baseColor = baseColors[currentIndex % baseColors.length];
      const variation = result.length % 3;
      
      // Create variations - lighter, darker, or more saturated
      if (variation === 0) {
        // Lighter variation
        result.push(chartColors.withOpacity(baseColor, 0.7));
      } else if (variation === 1) {
        // Darker variation (fake it by adding some black)
        result.push(chartColors.withOpacity('#000000', 0.3) + ' ' + baseColor);
      } else {
        // More saturated (fake it with shadow)
        result.push(baseColor + ' 0 0 5px ' + baseColor);
      }
      
      currentIndex++;
    }
    
    return result;
  }
};

// More visually consistent and pleasing data visualization color schemes
export const colorSchemes = {
  // Color scheme for country comparisons
  countries: {
    us: chartColors.us,
    cn: chartColors.cn,
    focusCountry: chartColors.focusCountry,
    rest: chartColors.rest
  },
  
  // Color scheme for institution types
  institutions: {
    academic: chartColors.academic,
    corporate: chartColors.corporate,
    unknown: chartColors.muted
  },
  
  // Color scheme for paper categories
  papers: {
    regular: chartColors.papers,
    spotlight: chartColors.spotlight,
    oral: chartColors.oral
  },
  
  // Color scheme for author data
  authors: {
    firstAuthor: chartColors.academic,
    coAuthor: chartColors.corporate,
    nonFocusCountry: chartColors.muted
  }
};

export default chartColors;
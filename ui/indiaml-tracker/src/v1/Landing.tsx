import React, { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Github, Search, ChevronRight, TrendingUp, Database, Award, Cpu } from 'lucide-react';

const HomePage = () => {
  const mapRef = useRef(null);
  
  useEffect(() => {
    if (mapRef.current) {
      drawDotGrid();
    }
  }, []);
  
  const drawDotGrid = () => {
    const canvas = mapRef.current;
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    ctx.clearRect(0, 0, width, height);
    
    // Draw dot grid
    const spacing = 20;
    ctx.fillStyle = 'rgba(100, 116, 240, 0.3)';
    
    for (let x = 0; x < width; x += spacing) {
      for (let y = 0; y < height; y += spacing) {
        ctx.beginPath();
        ctx.arc(x, y, 1, 0, Math.PI * 2);
        ctx.fill();
      }
    }
    
    // Draw India with brighter dots
    const indiaCoords = [
      {x: width * 0.65, y: height * 0.48},
      {x: width * 0.67, y: height * 0.46},
      {x: width * 0.66, y: height * 0.47},
      {x: width * 0.68, y: height * 0.49},
      {x: width * 0.67, y: height * 0.5},
      {x: width * 0.66, y: height * 0.51},
      {x: width * 0.65, y: height * 0.5},
      {x: width * 0.64, y: height * 0.49},
    ];
    
    ctx.fillStyle = 'rgba(255, 215, 0, 0.8)';
    indiaCoords.forEach(coord => {
      ctx.beginPath();
      ctx.arc(coord.x, coord.y, 2.5, 0, Math.PI * 2);
      ctx.fill();
    });
    
    // Draw connection lines from India to other tech hubs
    const techHubs = [
      {x: width * 0.2, y: height * 0.4},  // US West
      {x: width * 0.3, y: height * 0.35}, // US East
      {x: width * 0.45, y: height * 0.3}, // Europe
      {x: width * 0.75, y: height * 0.4}, // China
      {x: width * 0.8, y: height * 0.6},  // Australia
    ];
    
    const indiaCenter = {x: width * 0.66, y: height * 0.48};
    
    ctx.strokeStyle = 'rgba(100, 116, 240, 0.4)';
    ctx.lineWidth = 0.5;
    
    techHubs.forEach(hub => {
      ctx.beginPath();
      ctx.moveTo(indiaCenter.x, indiaCenter.y);
      ctx.lineTo(hub.x, hub.y);
      ctx.stroke();
      
      // Draw hub dot
      ctx.fillStyle = 'rgba(100, 116, 240, 0.6)';
      ctx.beginPath();
      ctx.arc(hub.x, hub.y, 2, 0, Math.PI * 2);
      ctx.fill();
    });
  };
  
  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.2,
        delayChildren: 0.3
      }
    }
  };
  
  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: { duration: 0.5, ease: "easeOut" }
    }
  };
  
  const pulseVariants = {
    pulse: {
      scale: [1, 1.05, 1],
      opacity: [0.7, 1, 0.7],
      transition: {
        duration: 2,
        repeat: Infinity,
        ease: "easeInOut"
      }
    }
  };
  
  const floatVariants = {
    float: {
      y: [0, -10, 0],
      transition: {
        duration: 3,
        repeat: Infinity,
        ease: "easeInOut"
      }
    }
  };
  
  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Hero Section */}
      <motion.div 
        className="relative overflow-hidden pt-16 pb-24"
        initial="hidden"
        animate="visible"
        variants={containerVariants}
      >
        {/* Background Map */}
        <div className="absolute inset-0 z-0 opacity-20">
          <canvas 
            ref={mapRef} 
            width={1200} 
            height={600} 
            className="w-full h-full"
          />
        </div>
        
        <div className="container mx-auto px-4 relative z-10">
          <motion.div 
            className="max-w-4xl mx-auto text-center mb-16"
            variants={itemVariants}
          >
            <motion.div 
              className="inline-block mb-6"
              animate="float"
              variants={floatVariants}
            >
              <div className="w-16 h-16 mx-auto bg-indigo-600 rounded-full flex items-center justify-center">
                <Cpu size={32} className="text-white" />
              </div>
            </motion.div>
            
            <motion.h1 
              className="text-5xl md:text-6xl font-bold mb-6 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-600"
              variants={itemVariants}
            >
              India's Rise in Machine Learning
            </motion.h1>
            
            <motion.p 
              className="text-xl text-gray-300 mb-8 leading-relaxed"
              variants={itemVariants}
            >
              Tracking India's growing contributions to the global AI/ML landscape.
              From groundbreaking research papers to innovative startups, discover how
              Indian researchers and engineers are shaping the future of technology.
            </motion.p>
            
            <motion.div 
              className="flex flex-wrap justify-center gap-4"
              variants={itemVariants}
            >
              <motion.a
                href="/papers-2024"
                className="px-8 py-4 bg-indigo-600 text-white rounded-lg font-medium flex items-center space-x-2 hover:bg-indigo-700 transition duration-300"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Search size={20} />
                <span>Explore NeurIPS and ICML 2024</span>
              </motion.a>
              
              <motion.a
                href="https://github.com/indiaml/research-data"
                target="_blank"
                rel="noopener noreferrer"
                className="px-8 py-4 bg-gray-800 text-white rounded-lg font-medium flex items-center space-x-2 hover:bg-gray-700 transition duration-300"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Github size={20} />
                <span>View on GitHub</span>
              </motion.a>
            </motion.div>
          </motion.div>
          
          {/* Stats Counter */}
          <motion.div 
            className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-24"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
          >
            <StatsCard 
              number="200+" 
              label="Research Papers" 
              icon={<Database size={24} />}
            />
            <StatsCard 
              number="10+" 
              label="Institutions" 
              icon={<Award size={24} />}
            />
            <StatsCard 
              number="500+" 
              label="Researchers" 
              icon={<Cpu size={24} />}
            />
            <StatsCard 
              number="$1M+" 
              label="AI Funding" 
              icon={<TrendingUp size={24} />}
            />
          </motion.div>
        </div>
      </motion.div>
      
      {/* Featured Papers Section */}
      <motion.div 
        className="py-16 bg-gray-800"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5, duration: 0.8 }}
      >
        <div className="container mx-auto px-4">
          <motion.div 
            className="flex justify-between items-center mb-12"
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.6 }}
          >
            <h2 className="text-3xl font-bold">Latest Research Papers</h2>
            <motion.a
              href="/papers-2024"
              className="flex items-center text-indigo-400 hover:text-indigo-300 transition-colors"
              whileHover={{ x: 5 }}
            >
              View all papers <ChevronRight size={20} />
            </motion.a>
          </motion.div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <PaperCard 
              title="Accuracy is Not All You Need"
              authors={["Abhinav Dutta", "Sanjeev Krishnan", "Nipun Kwatra"]}
              conference="NeurIPS 2024"
              delay={0.7}
            />
          
            <PaperCard 
              title="AutoMix: Automatically Mixing Language Models"
              authors={["Rishab Parthasarathy", "Aniruddha Mahapatra"]}
              conference="NeurIPS 2024"
              delay={0.9}
            />
            
            <PaperCard 
              title="BRAIn: Bayesian Reward-conditioned Amortized Inference for natural language generation from feedback"
              authors={["Divyansh Jhunjhunwala", "Aaditya Gupta"]} 
              conference="ICML 2024"
              delay={1.}
            />
          </div>
        </div>
      </motion.div>
      
      {/* Our Story */}
      <motion.div 
        className="py-20 bg-gray-900"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.2, duration: 0.8 }}
      >
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto">
            <motion.h2 
              className="text-3xl font-bold mb-8 text-center"
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 1.3 }}
            >
              Our Motivation
            </motion.h2>
            
            <motion.div 
              className="prose prose-lg prose-invert mx-auto"
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 1.4 }}
            >
              <p>
                The IndiaML Tracker was born from a simple tweet and grew into a mission to spotlight
                India's contributions to the global machine learning landscape.
              </p>
              
              <div className="my-8 p-6 bg-gray-800 rounded-lg">
                <h3 className="text-xl font-semibold mb-4">The Tweet That Started It All</h3>
                <p>
                  Paras Chopra, Founder of <a href="https://lossfunk.com">Lossfunk</a>, tweeted asking if anyone was interested in building a platform to track India's contributions
                  to machine learning.
                </p>
              </div>
              
              <div className="my-8 p-6 bg-gray-800 rounded-lg">
                <h3 className="text-xl font-semibold mb-4">From Idea to Reality</h3>
                <p>
                  <a href="https://iamsohan.in">Sohan Basak</a>, who loves tech and AI/ML, responded to the challenge and quickly built the first version of the
                  tracker.
                </p>
              </div>
              
              <div className="my-8 p-6 bg-gray-800 rounded-lg">
                <h3 className="text-xl font-semibold mb-4">Collaboration Begins</h3>
                <p>
                  After Paras retweeted the project, they exchanged contacts and formed a partnership to develop the platform further.
                </p>
              </div>
            </motion.div>
          </div>
        </div>
      </motion.div>
      
      {/* Call to Action */}
      <motion.div 
        className="py-16 bg-indigo-900"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1.5, duration: 0.8 }}
      >
        <div className="container mx-auto px-4 text-center">
          <motion.h2 
            className="text-3xl font-bold mb-6"
            animate="pulse"
            variants={pulseVariants}
          >
            Join the Movement
          </motion.h2>
          
          <motion.p 
            className="text-xl text-indigo-200 mb-8 max-w-2xl mx-auto"
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 1.6 }}
          >
            Help us track and celebrate India's contributions to the global AI/ML community.
            Submit papers, suggest features, or contribute to our open-source project.
          </motion.p>
          
          <motion.div 
            className="flex flex-wrap justify-center gap-4"
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 1.7 }}
          >
            <motion.a
              href="/contribute"
              className="px-8 py-4 bg-white text-indigo-900 rounded-lg font-medium hover:bg-gray-100 transition duration-300"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Contribute Data
            </motion.a>
            
            <motion.a
              href="/newsletter"
              className="px-8 py-4 bg-transparent border-2 border-white text-white rounded-lg font-medium hover:bg-white hover:text-indigo-900 transition duration-300"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Join Newsletter
            </motion.a>
          </motion.div>
        </div>
      </motion.div>
    </div>
  );
};

// Stats Card Component
const StatsCard = ({ number, label, icon }) => {
  return (
    <motion.div 
      className="bg-gray-800 rounded-lg p-6"
      variants={{
        hidden: { y: 20, opacity: 0 },
        visible: { 
          y: 0, 
          opacity: 1,
          transition: { duration: 0.5, ease: "easeOut" }
        }
      }}
      whileHover={{ 
        y: -5,
        boxShadow: "0 10px 25px -5px rgba(66, 153, 225, 0.1)"
      }}
    >
      <div className="w-12 h-12 bg-indigo-800 rounded-lg flex items-center justify-center mb-4">
        {icon}
      </div>
      <h3 className="text-3xl font-bold mb-2">{number}</h3>
      <p className="text-gray-400">{label}</p>
    </motion.div>
  );
};

// Paper Card Component
const PaperCard = ({ title, authors, conference, delay }) => {
  return (
    <motion.div 
      className="bg-gray-800 rounded-lg overflow-hidden hover:bg-gray-750 transition-colors"
      initial={{ y: 30, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ delay, duration: 0.6 }}
      whileHover={{ y: -5 }}
    >
      <div className="p-6">
        <div className="text-sm text-indigo-400 mb-2">{conference}</div>
        <h3 className="text-xl font-semibold mb-4">{title}</h3>
        <div className="flex flex-wrap gap-2 mb-4">
          {authors.map((author, index) => (
            <span 
              key={index}
              className="px-3 py-1 bg-gray-700 rounded-full text-sm"
            >
              {author}
            </span>
          ))}
        </div>
        <motion.a
          href="#"
          className="inline-flex items-center text-indigo-400 hover:text-indigo-300"
          whileHover={{ x: 5 }}
        >
          View PDF <ChevronRight size={16} className="ml-1" />
        </motion.a>
      </div>
    </motion.div>
  );
};

export default HomePage;